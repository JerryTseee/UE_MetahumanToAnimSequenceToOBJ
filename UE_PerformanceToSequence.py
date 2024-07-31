import unreal
import argparse
import sys
import os
import json
import tkinter as tk
from tkinter import filedialog


def create_performance_asset(path_to_identity : str, path_to_capture_data : str, save_performance_location : str) -> unreal.MetaHumanPerformance:
    
    capture_data_asset = unreal.load_asset(path_to_capture_data)
    identity_asset = unreal.load_asset(path_to_identity)
    performance_asset_name = "{0}_Performance".format(capture_data_asset.get_name())

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    performance_asset = asset_tools.create_asset(asset_name=performance_asset_name, package_path=save_performance_location, 
                                                 asset_class=unreal.MetaHumanPerformance, factory=unreal.MetaHumanPerformanceFactoryNew())

    
    performance_asset.set_editor_property("identity", identity_asset)# load into the identity setting
    performance_asset.set_editor_property("footage_capture_data", capture_data_asset)# load into the capture footage setting

    return performance_asset



def run_animation_export(output_order, performance_asset : unreal.MetaHumanPerformance):
    
    performance_asset_name = "AS"+str(output_order)# this is the name of the animation sequence, can be changed
    unreal.log("Exporting animation sequence for Performance '{0}'".format(performance_asset_name))

    export_settings = unreal.MetaHumanPerformanceExportAnimationSettings()
    export_settings.enable_head_movement = False# Enable or disable to export the head rotation
    export_settings.show_export_dialog = False
    export_settings.export_range = unreal.PerformanceExportRange.PROCESSING_RANGE
    anim_sequence: unreal.AnimSequence = unreal.MetaHumanPerformanceExportUtils.export_animation_sequence(performance_asset, export_settings)
    unreal.log("Exported Anim Sequence {0}".format(performance_asset_name))




def process_shot(output_order, performance_asset : unreal.MetaHumanPerformance, export_level_sequence : bool, export_sequence_location : str,
                 path_to_meta_human_target : str, start_frame : int = None, end_frame : int = None):
    
    performance_asset_name = "AS"+str(output_order)# this is the name of the animation sequence, can be changed

    if start_frame is not None:
        performance_asset.set_editor_property("start_frame_to_process", start_frame)

    if end_frame is not None:
        performance_asset.set_editor_property("end_frame_to_process", end_frame)

    #Setting process to blocking will make sure the action is executed on the main thread, blocking it until processing is finished
    process_blocking = True
    performance_asset.set_blocking_processing(process_blocking)

    unreal.log("Starting MH pipeline for '{0}'".format(performance_asset_name))
    startPipelineError = performance_asset.start_pipeline()
    if startPipelineError is unreal.StartPipelineErrorType.NONE:
        unreal.log("Finished MH pipeline for '{0}'".format(performance_asset_name))
    elif startPipelineError is unreal.StartPipelineErrorType.TOO_MANY_FRAMES:
        unreal.log("Too many frames when starting MH pipeline for '{0}'".format(performance_asset_name))
    else:
        unreal.log("Unknown error starting MH pipeline for '{0}'".format(performance_asset_name))

    #export the animation sequence
    run_animation_export(output_order, performance_asset)






def run(output_order, number, end_frame):
    
    #load into the metahuman identity and capture footage, then output a metahuman performance
    performance_asset = create_performance_asset(
        path_to_identity="/Game/MetaHumans/vasilisa_MI2", # can be changed
        path_to_capture_data="/Game/MetaHumans/va"+str(number)+"_Ingested/006Vasilisa_"+str(number), # can be changed
        save_performance_location="/Game/Test/") # can be changed
    
    #process the metahuman performance and export the animation sequence
    process_shot(
        output_order=output_order,
        performance_asset=performance_asset,
        export_level_sequence=True,
        export_sequence_location="/Game/Test/", # can be changed
        path_to_meta_human_target="/Game/MetaHumans/Cooper", # can be changed
        start_frame=0,
        end_frame=end_frame)
    




# function to get the current level sequence and the sequencer objects
def get_sequencer_objects(level_sequence):
	world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
	#sequence_asset = unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
	sequence_asset = level_sequence
	range = sequence_asset.get_playback_range()
	sequencer_objects_list = []
	sequencer_names_list = []
	bound_objects = []

	sequencer_objects_list_temp = unreal.SequencerTools.get_bound_objects(world, sequence_asset, sequence_asset.get_bindings(), range)

	for obj in sequencer_objects_list_temp:
		bound_objects = obj.bound_objects

		if len(bound_objects)>0:
			if type(bound_objects[0]) == unreal.Actor:
				sequencer_objects_list.append(bound_objects[0])
				sequencer_names_list.append(bound_objects[0].get_actor_label())
	return sequence_asset, sequencer_objects_list, sequencer_names_list



# function to export the face animation keys to a json file
def mgMetaHuman_face_keys_export(level_sequence, output_path):
	system_lib = unreal.SystemLibrary()
	root = tk.Tk()
	root.withdraw()

	face_anim = {}

	world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

	sequence_asset, sequencer_objects_list,sequencer_names_list = get_sequencer_objects(level_sequence)
	face_possessable = None

	editor_asset_name = unreal.EditorAssetLibrary.get_path_name_for_loaded_asset(sequence_asset).split('.')[-1]
	
	for num in range(0, len(sequencer_names_list)):
		actor = sequencer_objects_list[num]
		asset_name = actor.get_actor_label()
		bp_possessable = sequence_asset.add_possessable(actor)
		child_possessable_list = bp_possessable.get_child_possessables()
		character_name = ''

		for current_child in child_possessable_list:
			if 'Face' in current_child.get_name():
				face_possessable = current_child
		
		if face_possessable:
			character_name = (face_possessable.get_parent().get_display_name())
			face_possessable_track_list = face_possessable.get_tracks()
			face_control_rig_track = face_possessable_track_list[len(face_possessable_track_list)-1]
			face_control_channel_list = unreal.MovieSceneSectionExtensions.get_all_channels(face_control_rig_track.get_sections()[0])
			face_control_name_list = []

			for channel in face_control_channel_list:
				channel_name = str(channel.get_name())
				channel_string_list = channel_name.split('_')
				channel_name = channel_name.replace('_' + channel_string_list[-1], '')
				face_control_name_list.append(channel_name)

			for ctrl_num in range(0, len(face_control_channel_list)):
				control_name = face_control_name_list[ctrl_num]

				try:
					numKeys = face_control_channel_list[ctrl_num].get_num_keys()
					key_list = [None] * numKeys
					keys = face_control_channel_list[ctrl_num].get_keys()
					for key in range(0, numKeys):
						key_value = keys[key].get_value()
						key_time = keys[key].get_time(time_unit=unreal.SequenceTimeUnit.DISPLAY_RATE).frame_number.value
						key_list[key]=([key_value, key_time])

					face_anim[control_name] = key_list
				except:
					face_anim[control_name] = []
			
			character_name = str(character_name)
			if 'BP_' in character_name:
				character_name = character_name.replace('BP_', '')
			if 'BP ' in character_name:
				character_name = character_name.replace('BP ', '')

			character_name = character_name.lower()
			print('character_name is ' + character_name)
            
			
			folder_path = output_path
			os.makedirs(folder_path, exist_ok=True)
			file_path = os.path.join(folder_path, f'{editor_asset_name}_face_anim.json')
			with open(file_path, 'w') as keys_file:
				keys_file.write('anim_keys_dict = ')
				keys_file.write(json.dumps(face_anim))
				
			
			
			print('Face Animation Keys output to: ' + str(keys_file.name))
		else:
			print(editor_asset_name)
			print('is not a level sequence. Skipping.')





#path that contains video data, start to process performance
path = "F:\\Jerry\\Vasilisa" #can be changed
output_order = 1

for i in os.listdir(path):
    set_path = os.path.join(path, i)

    if os.path.isdir(set_path):
        #get the current folder number
        folder_number = int(i.split("_")[-1])

        json_file_path = os.path.join(set_path, "take.json")

        if os.path.isfile(json_file_path):
            with open(json_file_path, "r") as file:
                data = json.load(file)
            end_frame = data["frames"]
            end_frame = end_frame // 2 + 1
            run(output_order, folder_number, end_frame)
            print("The performance process is done!")
            output_order += 1







# The start the second part: create the level sequence and export the sequence
# add a new actor into the world
actor_path = "/Game/MetaHumans/Cooper/BP_Cooper" # the path of the actor, can be changed
actor_class = unreal.EditorAssetLibrary.load_blueprint_class(actor_path)
coordinate = unreal.Vector(-25200.0, -25200.0, 100.0) # randomly put it on a coordinate of the world
editor_subsystem = unreal.EditorActorSubsystem()
new_actor = editor_subsystem.spawn_actor_from_class(actor_class, coordinate)



animation_sequence = dict()
#assume the dataset is only 50 folders !!! Important, need to be changed base on real dataset number!! And number order should be 1, 2, 3, 4, ... ...
for i in range(1,50):
    animation_sequence[i] = False

path = "F:\\Jerry\\Vasilisa" #folder that contain all the character folders, need to be changed base on the real path, can be changed

#for every character folder, start to do the work:
for i in os.listdir(path):
    set_path = os.path.join(path, i) #the path of each specific character folder
    if os.path.isdir(set_path):
        #if it is indeed a directory
        json_file_path = os.path.join(set_path, "take.json")
        if os.path.isfile(json_file_path):
            #if the json file exists -> create a new level sequence -> set the playback range
            with open(json_file_path) as file:
                data = json.load(file)
            
            frames_value = data["frames"]
            value = frames_value // 2 + 1 #this is the upper bound of the frame range

            #create a new level sequence
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

            asset_name = set_path.split("\\")[-1] #get the last part of the path

            level_sequence = unreal.AssetTools.create_asset(asset_tools, asset_name, package_path = "/Game/", asset_class = unreal.LevelSequence, factory = unreal.LevelSequenceFactoryNew())
            
            level_sequence.set_playback_start(0) #starting frame will always be 0
            
            level_sequence.set_playback_end(value) #end


            #start to load into the animation to the current face track:
            #Need to be changed base on the real name
            face_anim_path = "/Game/Test/AS_006Vasilisa_"
            #then from low to high to load the animation sequence into the current face track (if the sequenced is loaded before, it will not be loaded again, then go the next)
            for i in range(26,50):#And number order of the animation file should be continueing!!!
                final_face_anim_path = face_anim_path + str(i) + "_Performance"
                if final_face_anim_path:#if the path exists
                    if animation_sequence[i] == False:#if the animation sequence is not used before
                        animation_sequence[i] = True
                        anim_asset = unreal.EditorAssetLibrary.load_asset(final_face_anim_path)
                        print("animation sequence:" + str(anim_asset))
                        break
                else:
                    continue


            anim_asset = unreal.AnimSequence.cast(anim_asset)
            params = unreal.MovieSceneSkeletalAnimationParams()
            params.set_editor_property("Animation", anim_asset)

            #add the actor into the level sequence
            actor_binding = level_sequence.add_possessable(new_actor)
            transform_track = actor_binding.add_track(unreal.MovieScene3DTransformTrack)
            anim_track = actor_binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)

            # Add section to track to be able to manipulate range, parameters, or properties
            transform_section = transform_track.add_section()
            anim_section = anim_track.add_section()

            # Get level sequence start and end frame
            start_frame = level_sequence.get_playback_start()
            end_frame = level_sequence.get_playback_end()

            # Set section range to level sequence start and end frame
            transform_section.set_range(start_frame, end_frame)
            anim_section.set_range(start_frame, end_frame)

            #add face animation track
            components = new_actor.get_components_by_class(unreal.SkeletalMeshComponent)
            print("Components of Cooper: ")
            print(components)

            face_component = None
            for component in components:
                if component.get_name() == "Face":
                    face_component = component
                    break

            print(face_component)


            #get the face track (same technique as above):
            face_binding = level_sequence.add_possessable(face_component)
            print(face_binding)
            transform_track2 = face_binding.add_track(unreal.MovieScene3DTransformTrack)
            anim_track2 = face_binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
            transform_section2 = transform_track2.add_section()
            anim_section2 = anim_track2.add_section()
            anim_section2.set_editor_property("Params", params)#add animation
            transform_section2.set_range(start_frame, end_frame)
            anim_section2.set_range(start_frame, end_frame)


            # bake to control rig to the face
            print("level sequence: " + str(level_sequence))

            editor_subsystem = unreal.UnrealEditorSubsystem()
            world = editor_subsystem.get_editor_world()
            print("world: " + str(world))

            anim_seq_export_options = unreal.AnimSeqExportOption()
            print("anim_seq_export_options: " + str(anim_seq_export_options))

            control_rig = unreal.load_object(name = '/Game/MetaHumans/Common/Face/Face_ControlBoard_CtrlRig', outer = None)# can be changed
            control_rig_class = control_rig.get_control_rig_class()# use class type in the under argument
            print("control rig class: " + str(control_rig_class))
            
            unreal.ControlRigSequencerLibrary.bake_to_control_rig(world, level_sequence, control_rig_class = control_rig_class, export_options = anim_seq_export_options, tolerance = 0.01, reduce_keys = False, binding = face_binding)


		    # Refresh to visually see the new level sequence
            unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()


            # Export the current face animation keys to a json file
            output_path = "F:\\Jerry\\Vasilisa_sequence" # can be changed
            mgMetaHuman_face_keys_export(level_sequence, output_path)
            unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()

print("Well Done! Jerry!")
