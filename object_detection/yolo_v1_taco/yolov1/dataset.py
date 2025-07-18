import torch
# torch.set_printoptions(threshold=torch.inf) # shows all the values when printing tensors in jupyter notebook
import os
import pandas as pd
import gc # built-ing memory clean-up
from torchvision.transforms import Compose
from typing import Optional
from PIL import Image



class Dataset(torch.utils.data.Dataset):
    def __init__(self, S:int, B:int, C:int, whichDataset:str="train", transforms:Optional[Compose]=None):
        """
        Dataset Class
        
        Args:
            S : int
                Split size to create the grid on image. 7 -> 7^7 = 49 cells.
            B : int
                Number of boxes that each cell predicts. 
            C : int
                Number of classes.
            whichDataset : str
                "train", "test", or "valid". Which folder to grab the images and labels. Default: "train".
            transform : torchvision.transforms 
                Transform -> resize and normalize images.
        """
        self.whichDataset = whichDataset
        # get the labels and images dir
        self.labels_dir = os.path.join("./data", whichDataset, "labels")
        self.imgs_dir = os.path.join("./data", whichDataset, "images")
        self.create_csv_file()
        self.S = S
        self.B = B
        self.C = C
        self.transforms = transforms
        self.df = pd.read_csv(os.path.join("./data", whichDataset, "dataframe.csv"))
    
    def __len__(self): # returns the size of the entire dataset
        return len(self.df) # NOTE: maybe just storing the size of the dataset will save memory and will work, instead of keeping the df in memory
    
    def __getitem__(self, index) -> (Image, torch.Tensor):
        """
        Get a single image and its corresponding label matrix.

        Parameters
        ----------
            index: (int)
                the index of the image in the csv dataframe list
        Returns
        -------
            tuple : ( PIL.image, tensor) 
                (Single image, label bounding box matrix). The label tensor is of shape (S, S, NUM_NODES_PER_CELL).                
        """
        # get the bboxes from the .txt file
        label_path = os.path.join(self.labels_dir, self.df.iloc[index,1])
        bboxes = []
        with open(label_path) as f:
            for label in f.readlines():
                class_label, x, y, width, height = [
                    float(x) if float(x) != int(float(x)) else int(x)
                    for x in label.replace("\n", "").split()
                ]
                bboxes.append([class_label, x, y, width, height])
        bboxes = torch.tensor(bboxes)

        # open the image
        image = Image.open(os.path.join(self.imgs_dir, self.df.iloc[index, 0]))

        # #######
        # TODO MAKE SURE THAT THE BBOXES ARE IN PERCENTAGE VALUES BEFORE APPLYING TRANSFORMS OR ELSE IT MESS UP EVERYTHING.
        # #######

        if self.transforms: # apply transform
            image, bboxes = self.transforms(image, bboxes)

        # NOTE we will make the shape of the label tensors the same as the model's output, this is to make the code dry. The label's second bounding box nodes will not be used. Below -> self.B * 5 + self.C. Example: 18+5*2=28, Second bbox -> pc_2, x, y, w, h
        label_matrix = torch.zeros((self.S, self.S, self.B * 5 + self.C ))
        # ==> Add the bboxes data to the label_matrix
        for box in bboxes:
            class_label, x, y, width, height = box.tolist()

            # find which cell the box's midpoint is in
            # i, j represents (row, col), locates the cell that contains the bbox's mid-point.
            i, j = int(self.S * y), int(self.S * x)

            # NOTE Resize the X and Y coordinates to be relative to the cell instead of the entire image. HOWEVER we don't do this for the width and height!
            #       x, y can not be bigger than 1 that would mean its larger than the cell, however the height and width of the bbox can be bigger than 1.
            x_rel_cell, y_rel_cell = self.S * x - j, self.S * y - i

            # TODO did I add a 1 to class_idx????
            
            if label_matrix[i, j, self.C] == 0: # checking if theres currently no object in i and j, this is also the position of the first probability_score
                # NOTE: if two bounding boxes are in the same cell then only one will be selected. This is less likely to occur if split_size is large ex:19x19.
                label_matrix[i, j, self.C] = 1 # Set this cell is now taken, meaning a bbox occupies it.
                box_coordinates = torch.tensor(
                    [x_rel_cell, y_rel_cell, width, height]
                )
                # Add the bbox coordinates at the bbox1_x_y_w_h in the label matrix
                label_matrix[i, j, self.C + 1 : self.C + 1 + 4] = box_coordinates
                # Add the class label
                label_matrix[i, j, int(class_label)] = 1 
        return image, label_matrix

    def create_csv_file(self):
        """Create a CSV file that contains a dataframe of corresponding image and label filenames by row."""
        filename = f"./data/{self.whichDataset}/dataframe.csv"
        # check if we already create the csv dataframe
        print("Checking csv dataframe file:", end=" ")
        if os.path.exists(filename):
            print("csv dataframe file already exists.")
            return 
        
        # Get all image and label filenames and store in a list
        image_files = sorted([f for f in os.listdir(self.imgs_dir) if os.path.isfile(os.path.join(self.imgs_dir, f))])
        label_files = sorted([f for f in os.listdir(self.labels_dir) if os.path.isfile(os.path.join(self.labels_dir, f))])

        # Match files by name
        matched_data = []
        
        for img_f in image_files:
            label_f = img_f.rsplit(".", 1)[0] + ".txt" # grab the image filename but remove the .jpg and add .txt extension
            if label_f in label_files: # check if the filename exists in the label directory
                matched_data.append({
                    "img": img_f,
                    "label": label_f
                })
        df = pd.DataFrame(matched_data)
        df.to_csv(filename, index=False)
        del df # delete the dataframe to save memory
        gc.collect() # clean up-memory



 