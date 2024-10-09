import os
import sys
import imp
import json
import maya.cmds as cmds



#define the function to import the animation sequence from the selected json file
def mgApplyFaceMocap(filePath):
    objLs = cmds.ls(sl=1)
    namespace = ''
        
    if len(objLs)>0:
        if ':' in objLs[0]:
            namespace = objLs[0].split(':')[0] + ':'
        else:
            namespace = ''
    anim_keys_file = imp.load_source('', filePath)
    
    anim_keys = anim_keys_file.anim_keys_dict
    
    for dict_key in anim_keys:
        keyframes_list = anim_keys[dict_key]
        ctrl = dict_key
        attr = 'translateY'
        if '.' in ctrl:
            ctrl_string_list = ctrl.split('.')
            ctrl = ctrl_string_list[0]
            if len(ctrl_string_list)>2:
                attr = ctrl_string_list[1].replace('Location', 'translate').replace('Rotation', 'rotate').replace('Scale', 'scale') + ctrl_string_list[-1].upper()
            else:
                attr = 'translate' + ctrl_string_list[-1].upper()

        # check for numbers at the end of cntrl name
        
        ctrl_name = ctrl
        if ctrl_name.split('_')[-1].isdigit():
            ctrl_name = ctrl_name.replace('_' + ctrl_name.split('_')[-1], '')
        ctrl_name = namespace + ctrl_name

        if cmds.objExists(ctrl_name):
            for key_num in range(0,len(keyframes_list)):
                key_val = keyframes_list[key_num]
                cmds.setKeyframe(ctrl_name, attribute=attr, v = key_val[0], t=key_val[1] )
        else:
            print('Skipping ' + ctrl_name + ' as no such object exists.')
            
    print('Applied Animation to Face Rig.')



#define a function to get the frame value of the selected video
def get_frame_numbers(filePath):
    # Read the contents of the file
    with open(filePath, "r") as file:
        content = file.read()

    # Extract the JSON content by removing the variable assignment
    json_content = content.split("=", 1)[-1].strip()
    # Parse the extracted JSON content
    parsed_data = json.loads(json_content)

    #just simply use the parsed data, not re-reading the file
    key_list = list(parsed_data.keys())
    first_key = key_list[0]

    length = len(parsed_data[first_key])
    return length



#define a function to export the OBJ files into the destination
def export_obj_sequence(export_dir, frame_start, frame_end):
    selection = cmds.ls(selection=True)

    if not selection:
        #end of the export
        print("Nothing selected, nothing to export")
        return

    if not os.path.isdir(export_dir):
        #if no such destination file, then end
        print("Specified directory doesn't exist:", export_dir)
        return

    #start to export
    for i in range(frame_start, frame_end + 1):
        try:
            cmds.currentTime(i, edit=True)
        except:
            print("Couldn't go to frame", i)
            raise

        # Generate the filename based on the frame number
        filename = os.path.join(export_dir, 'Object_{:03d}.obj'.format(i))

        try:
            cmds.file(filename, save=False, force=True, exportSelected=True, type="OBJexport")
        except:
            print("Couldn't save file:", filename)
            raise

        print("Exported:", filename)






def process_multiple_animation_sequences(sequence_dir, export_dir):
    #get the list of animation sequence files in the selected directory
    sequence_files = os.listdir(sequence_dir)

    #sort them
    sequence_files.sort()

    #create a new folder to store the exported OBJ files
    folder_counter = 1
    folder_name = os.path.join(export_dir, "Set_{}".format(folder_counter))
    os.makedirs(folder_name, exist_ok=True)

    for sequence in sequence_files:
        #construct the paths
        sequence_path = os.path.join(sequence_dir, sequence)

        #start to process
        if sequence.endswith(".json"):
            #calling all function!!! Let's go!!!
            mgApplyFaceMocap(sequence_path)
            frame_number = get_frame_numbers(sequence_path)
            export_obj_sequence(folder_name, 1, frame_number)#export the newly created folder
            print("Successful!")

            if folder_counter < len(sequence_files):
                folder_counter += 1
                folder_name = os.path.join(export_dir, "Set_{}".format(folder_counter))
                os.makedirs(folder_name, exist_ok=True)

        else:
            print("Skip the mismatched file: "+sequence)



sequence_dir = "F:\\Jerry\\animation_sequences"
export_dir = "F:\\Jerry\\Automation_Multiple_Maya_OBJ"

#call the function
process_multiple_animation_sequences(sequence_dir, export_dir)
