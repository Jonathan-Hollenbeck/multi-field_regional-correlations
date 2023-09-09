import os
import shutil

SOURCE_FILES_PATH = "../GrandEnsemble/temparature_surface_anomaly/rcp85"
DESTINATION_PATH = "../GrandEnsemble/temparature_surface_anomaly/copiedruns"

files_list = os.listdir(SOURCE_FILES_PATH)

for i in range(len(files_list)):
    run_path = DESTINATION_PATH + "/" + str(i)
    if os.path.exists(run_path):
        shutil.rmtree(run_path)
    os.mkdir(run_path)

    file_path = SOURCE_FILES_PATH + "/" + files_list[i]

    shutil.copy(file_path, run_path)

    print(str(round(((i + 1) / len(files_list)) * 100, 0)) + "% | " + files_list[i] + " done")