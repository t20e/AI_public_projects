"""View example print statements for i_coords, j_coords, b_coords examples in the extract_bboxes()"""

"""@ below variable prints"""
i_coords, j_coords = torch.meshgrid(
    torch.arange(S, device=DEVICE), torch.arange(S, device=DEVICE), indexing="ij"
)  # (7, 7)


# if S=7, view in full screen
#              tensor([[0, 0, 0, 0, 0, 0, 0],              tensor([[0, 1, 2, 3, 4, 5, 6],
#                      [1, 1, 1, 1, 1, 1, 1],                      [0, 1, 2, 3, 4, 5, 6],
#                      [2, 2, 2, 2, 2, 2, 2],                      [0, 1, 2, 3, 4, 5, 6],
#       i_coords =     [3, 3, 3, 3, 3, 3, 3],       j_coords=      [0, 1, 2, 3, 4, 5, 6],
#                      [4, 4, 4, 4, 4, 4, 4],                      [0, 1, 2, 3, 4, 5, 6],
#                      [5, 5, 5, 5, 5, 5, 5],                      [0, 1, 2, 3, 4, 5, 6],
#                      [6, 6, 6, 6, 6, 6, 6]])                     [0, 1, 2, 3, 4, 5, 6]])


"""@ below variable prints"""
i_coords = i_coords.unsqueeze(-1).expand(-1, -1, B)  # from (7,7) -> (7, 7, 2)
j_coords = j_coords.unsqueeze(-1).expand(-1, -1, B)  # (7, 7, 2)
b_coords = torch.arange(B, device=DEVICE).view(1, 1, B).expand(S, S, B)  # (7, 7, 2)


#         tensor([ [[0, 0], ... [[6, 6],                tensor([ [ [0, 0],  ... [ [0, 0],
#                  [0, 0],  ...  [6, 6],                           [1, 1],  ...   [1, 1],
#                  [0, 0],  ...  [6, 6],                           [2, 2],  ...   [2, 2],
# i_coords =       [0, 0],  ...  [6, 6],   j_coords =              [3, 3],  ...   [3, 3],
#                  [0, 0],  ...  [6, 6],                           [4, 4],  ...   [4, 4],
#                  [0, 0],  ...  [6, 6],                           [5, 5],  ...   [5, 5],
#                  [0, 0]], ...  [6, 6]] ]                         [6, 6] ],...   [6, 6] ]


#                 [
#                     [[0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1]],
#                     [[0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1]],
# b_coords =           [[0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1]],
#                     [[0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1]],
#                     [[0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1]],
#                     [[0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1]],
#                     [[0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1]],
#                 ]
