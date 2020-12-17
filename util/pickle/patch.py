import os
import logging
from typing import List

from trigger_project.instances.opening_instance import OpeningInstance
from trigger_project.instances.user_instance import UserInstance


import io
import pickle


class RenameUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        renamed_module = module
        if module == "trigger.models.softskill":
            renamed_module = "trigger_project.models.softskill"
        elif module == "trigger.models.hardskill":
            renamed_module = "trigger_project.models.hardskill"
        elif module == "trigger.models.user":
            renamed_module = "trigger_project.models.user"
        elif module == "trigger.models.opening":
            renamed_module = "trigger_project.models.opening"
        elif module == "trigger.models.project":
            renamed_module = "trigger_project.models.project"
        elif module == "trigger.train.transformers.user_transformer":
            renamed_module = "trigger_project.instances.user_instance"
        elif module == "trigger.train.transformers.opening_transformer":
            renamed_module = "trigger_project.instances.opening_instance"
        elif module == "util.operation":
            renamed_module = "trigger_project.operation"
        

        return super(RenameUnpickler, self).find_class(renamed_module, name)


def renamed_load(file_obj):
    return RenameUnpickler(file_obj).load()


def renamed_loads(pickled_bytes):
    file_obj = io.BytesIO(pickled_bytes)
    return renamed_load(file_obj)


# What I did:
# Create files with a different name. (For example Softskill -> Softskillz)
# Read the old embeddings and replace old Softskill for new one
# Save
# Delete file with the correct name (Softskill)
# Rename Softskillz -> Softskill
# edit the find_class and add something like:

# elif module == "trigger.models.softskillz":
#            renamed_module = "trigger.models.softskill"

# Run this again

def rename_instances(instances_paths: List[str]):
    for instances_path in instances_paths:

        instances_files = [
            os.path.join(instances_path, f)
            for f in os.listdir(instances_path)
            if os.path.isfile(os.path.join(instances_path, f))
        ]

        users_instances_files = [
            instance_path
            for instance_path in instances_files
            if instance_path.find("users") != -1
        ]

        openings_instances_files = [
            instance_path
            for instance_path in instances_files
            if instance_path.find("openings") != -1
        ]

        for users_instances_path in users_instances_files:

            logging.info("Users instances " + users_instances_path)

            with open(users_instances_path, 'rb') as file:
                users_instances = renamed_load(file)

            UserInstance.save_instances(users_instances_path, users_instances)

        for openings_instances_path in openings_instances_files:

            logging.info("Opening instances " + openings_instances_path)

            with open(openings_instances_path, 'rb') as file:
                openings_instances = renamed_load(file)

            OpeningInstance.save_instances(openings_instances_path, openings_instances)

def rename_operations(operations_folder: str):
    for operations_test in os.listdir(operations_folder):

        instances_files = [
            os.path.join(os.path.join(operations_folder, operations_test, f))
            for f in os.listdir(os.path.join(operations_folder, operations_test))
            if os.path.isfile(os.path.join(operations_folder, operations_test, f))
        ]

        users_instances_files = [
            instance_path
            for instance_path in instances_files
            if instance_path.find("users") != -1
        ]

        openings_instances_files = [
            instance_path
            for instance_path in instances_files
            if instance_path.find("openings") != -1
        ]

        for users_instances_path in users_instances_files:

            logging.info("Users instances " + users_instances_path)

            with open(users_instances_path, 'rb') as file:
                users_instances = renamed_load(file)

            UserInstance.save_instances(users_instances_path, users_instances)

        for openings_instances_path in openings_instances_files:

            logging.info("Opening instances " + openings_instances_path)

            with open(openings_instances_path, 'rb') as file:
                openings_instances = renamed_load(file)

            OpeningInstance.save_instances(openings_instances_path, openings_instances)

def rename_projects(projects_folder: str):

    for projects_path in os.listdir(projects_folder):

        with open(os.path.join(projects_folder, projects_path), 'rb') as file:
            projects = renamed_load(file)

        with open(os.path.join(projects_folder, projects_path), 'wb') as file:
            pickle.dump(projects, file)

def correct_entity_id(instances_paths):
    for instances_path in instances_paths:

        instances_files = [
            os.path.join(instances_path, f)
            for f in os.listdir(instances_path)
            if os.path.isfile(os.path.join(instances_path, f))
        ]

        openings_instances_files = [
            instance_path
            for instance_path in instances_files
            if instance_path.find("openings") != -1
        ]

        for openings_instances_path in openings_instances_files:

            logging.info("Opening instances " + openings_instances_path)

            with open(openings_instances_path, 'rb') as file:
                openings_instances = pickle.load(file)

            for i, opening_instance in enumerate(openings_instances):
                opening_instance.opening.entityId = str(i)

            OpeningInstance.save_instances(openings_instances_path, openings_instances)
