import os
import glob
import numpy as np
import cv2
from yolo_segmentation import YOLOSegmentation
from shapely.geometry import Point, Polygon
import time

total_cow_count = 0
total_images = 1

def process_array(frame_data):
    print("Processing Started!")

    global total_images
    global number_of_arrays
    number_left = number_of_arrays - total_images
    print(f"Image #{total_images} out of {number_of_arrays}")
    print(f"{number_left} images left to process")

    ys = YOLOSegmentation("/home/agai/code/AgAI_CS/models/v8sSeg3_6_23.pt")

    image_count = 0
    total_cows = 0

    master_boxes = []

    coords_list = []

    normalized_data = cv2.normalize(frame_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    colored_data = cv2.applyColorMap(normalized_data, cv2.COLORMAP_BONE)

    file_save = "/mnt/data/countimages/orig/" + str(total_images) + ".jpg"
    print(f"Saving file at {file_save}")
    cv2.imwrite(file_save, colored_data)

    img = colored_data
    cow_count = 0
    total_calves = 0
    calf_count = 0
    person_count = 0

    cow_number = 0

    bboxes, classes, segmentations, scores = ys.detect(img)
    for bbox, class_id, seg, score in zip(bboxes, classes, segmentations, scores):
        cow_number += 1

        (x, y, x2, y2) = bbox
        
        if class_id == 0:
            # label = "cow"
            cow_count += 1
        elif class_id == 1:
            # label = "cow"
            calf_count += 1
            cow_count += 1
        elif class_id == 2:
            # label = "person"
            person_count += 1

        # Get the center of the bounding box
        try:
            min_x = np.min(seg, axis=0)[0]
            max_x = np.max(seg, axis=0)[0]
            min_y = np.min(seg, axis=0)[1]
            max_y = np.max(seg, axis=0)[1]
            center_x = int((min_x + max_x) / 2)
            center_y = int((min_y + max_y) / 2)
        except ValueError:
            # Handle the case where the array is empty
            min_x = 0
            max_x = 0
            min_y = 0
            max_y = 0
            center_x = 0
            center_y = 0

        # Get the value at the center coordinates
        value = frame_data[center_y, center_x]

        # Define the polygon
        try:
            polygon = Polygon(seg)
        except ValueError:
            polygon = None

        # Define the list of values inside the polygon
        if polygon is not None:
            values_inside_polygon = []
            for i in range(240):
                for j in range(320):
                    point = [j, i]
                    if polygon.contains(Point(point)):
                        # value = single_array[i, j]
                        value = frame_data[i, j]
                        values_inside_polygon.append(value)
        else:
            values_inside_polygon = None
        
        # Draw the polygon
        cv2.polylines(img, [seg], True, (0, 0, 255), 4)

        # Draw the bounding box
        # cv2.rectangle(img, (x, y), (x2, y2), (255, 0, 0), 2)

        # Write the Temperature on the image
        # cv2.putText(img, (str(label) + " " + str(int(np.mean(values_inside_polygon))) + "C"), (x, y - 10), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

        # Write the cow number on the image
        # cv2.putText(img, ("# "  + str(cow_number)), (x, y - 10), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)



        if values_inside_polygon is not None:
            mean_value = np.nanmean(values_inside_polygon)
            if np.isnan(mean_value):
                # Handle the case when the mean value is NaN (e.g., set a default value)
                mean_value = 0
        else:
            mean_value = None

        # Temperatures inside polygon
        if values_inside_polygon is not None:
            if len(values_inside_polygon) == 0:
                temp_mean = 200
            else:
                temp_mean = round(np.mean(values_inside_polygon), 1)
        else:
            temp_mean = None

        # Get all the temps inside polygon
        temp_all = []
        if values_inside_polygon is not None:
            for temp in values_inside_polygon:
                temp_all.append(round(temp, 1))

        coords = [class_id, score, temp_mean]
        # print(coords)

        coords_list.append(coords)

        single_detected = []

        single_detected = [cow_number, score, temp_mean]
        # print(single_detected)
        master_boxes.append(single_detected)

    cv2.imwrite("/mnt/data/countimages/detected/" + str(total_images) + ".jpg", img)

    total_images = total_images + 1
    
    message = f"Processed image: {image_count + 1} with {cow_count} cows"

    print(message)


    image_count += 1

    total_cows = total_cows + (cow_count)
    total_calves = total_calves + calf_count

    global total_cow_count 
    total_cow_count = total_cow_count + total_cows
    

# List all CSV files in the /mnt/data/count folder
folder_path = '/mnt/data/count'
csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

# Iterate through each file and read the numpy arrays
for file_path in csv_files:
    with open(file_path, 'r') as file:
        lines = file.readlines()

    arrays = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('2023'):
            array_data = lines[i+1:i+241]
            array = np.array([list(map(float, row.split())) for row in array_data])
            arrays.append(array)
            i += 241
        else:
            i += 1

    # Process each numpy array
    number_of_arrays = len(arrays)
    start_time = time.time()
    
    for array in arrays:
        start_array_time = time.time()
        process_array(array)
        end_array_time = time.time()
        array_time = end_array_time - start_array_time
        print(f"Time taken to single image: {array_time} seconds.")
        print("\n \n")
    
    end_time = time.time()

    total_time = end_time - start_time
    print(f"Total time taken to process all images: {total_time} seconds.")
    print(f"Average time per image: {total_time / number_of_arrays} seconds.")

print("Total Cows: ", (total_cow_count + 103))
print(f"In {total_images} images") 