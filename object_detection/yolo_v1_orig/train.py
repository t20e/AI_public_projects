import torch
import torch.optim as optim
from tqdm import tqdm
from typing import Optional

# My Modules
from configs.config_loader import YOLOConfig
from data.dataset_loader import dataset_loader
from model.model_utils import save_checkpoint
from model.loss import YOLOLoss
from model.yolov1 import YOLOv1
from utils.mAP import mAP  # Mean Average Precision


def train(
    cfg: YOLOConfig,
    yolo: YOLOv1,
    loader: dataset_loader,
    val_loader: Optional[dataset_loader],
    loss_fn: YOLOLoss,
    optimizer: optim,
    scheduler,
):
    """
    Train YOlO v1 model

    Args:
        cfg: Project Configurations.
        yolo: An instance of the YOLO model.
        loader: Train dataset loader.
        val_loader: Validation dataset loader.
        loss_fn: Loss function.
        optimizer: Optimizer.
        scheduler: Learning rate scheduler.
    """

    print("\n" + "#" * 64)
    print(f"\nTraining Model")
    print("\n" + "#" * 64)

    # If training from a checkpoint, start training from its last trained epoch to (max_epoch)
    max_epoch = cfg.LAST_EPOCH + cfg.EPOCHS
    mean_loss = 0  # Mean loss is the average loss for one epoch.

    for epoch in range(cfg.LAST_EPOCH + 1, max_epoch + 1):
        print("\n\n" + "|" + "-" * 64 + "|")
        print(f"Epoch: {epoch}/{max_epoch} | Lr = {optimizer.param_groups[0]['lr'] }")

        # === Helper function.
        # The mean_loss from mean_loss is the average loss for the current epoch.
        mean_loss = train_one_epoch(
            cfg=cfg, loader=loader, yolo=yolo, loss_fn=loss_fn, optimizer=optimizer
        )

        # === compute mean average precision every 10th epoch
        if epoch % 10 == 0:
            if cfg.COMPUTE_MEAN_AVERAGE_PRECISION:
                mean_average_per = mAP(cfg=cfg, val_loader=val_loader, yolo=yolo)
                # If the model has a good mAP save it, but not as a checkpoint.
                #   From paper: YOLO v1 achieved mAP score of 63.4 on the VOC 2007+2012 dataset. Paper text @ 'YOLO 2007+2012 63.4 45'.
                if mean_average_per > 63.4:
                    print(f"Model mAP score: {mean_average_per}")
                    pass

        # === Update Learning Rate: at the end of every epoch. Note: different learning rates need to be updated in different areas of code; example: OneCycleLR is done per-batch.
        if isinstance(scheduler, torch.optim.lr_scheduler.SequentialLR):
            scheduler.step()

    print(optimizer.param_groups[0]["lr"])

    # === Save model checkpoint.
    if cfg.SAVE_MODEL:
        if cfg.USE_SCHEDULER:
            scheduler_state = scheduler.state_dict()
        else:  # Dont save the scheduler
            scheduler_state = None
        save_checkpoint(
            state={
                "epoch": epoch,
                "model": yolo.state_dict(),
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler_state,
                "mean_loss": mean_loss,
            },
            epochs=epoch,
            loss=mean_loss,
            cfg=cfg,
        )


def train_one_epoch(cfg: YOLOConfig, loader, yolo, loss_fn, optimizer):
    """<- Helper function for each epoch. ->"""
    loop = tqdm(loader, leave=True)

    # --- Store the loss of the models bbox predictions vs true bboxes that it makes for every image.
    loss_history = []

    for batch_idx, (x, y) in enumerate(loop):
        """
        x: represents a batch of input data (images).
        y: represents the corresponding batch of ground truth labels bounding boxes for that image 'x'.
        Forward propagation:
             'x' (images) is passed through the model to get predictions. Initially, these predictions are random.
        Backpropagation:
            The model's internal parameters are adjusted based on the difference between its predictions and the true labels ('y') bounding boxes. This adjustment allows the model to progressively improve its ability to accurately predict labels.
        """
        # --- Move tensors to GPU
        x, y = x.to(cfg.DEVICE), y.to(
            cfg.DEVICE
        )  # x = (batch_size, 3, 448, 448) & y = (batch_size, 7, 7, 28)

        # === Forward-propagation | Predict
        out = yolo(x)  # (b_s, 1470)

        # --- Reshape output from (b_s, 1470) -> (batch_size, S, S, CELL_NODES).
        b_s = x.size(0)  # Batch size not hardcoded for worst-case.
        out = out.view(b_s, cfg.S, cfg.S, cfg.CELL_NODES)

        # === Backward-propagation | Gradient Descent
        #   Compute loss
        loss = loss_fn(out, y)
        loss_history.append(loss.item())

        #   Clear old gradients from the previous step batch otherwise they'd accumulate.
        optimizer.zero_grad()
        #   Compute gradients of the loss w.r.t. model parameters (via backpropagation) i.e -> Gradient Descent.
        loss.backward()
        optimizer.step()  # Update the model’s parameters using the computed gradients

        #   Update the progress bar
        loop.set_postfix(loss=loss.item())

    # --- Calculate the mean loss for the epoch
    epoch_mean_loss = sum(loss_history) / len(loss_history)
    print(f"Mean loss: {epoch_mean_loss}")
    return epoch_mean_loss
