from __future__ import annotations

from typing import Iterator, Generator
from dataclasses import dataclass
from pathlib import Path

from core.definitions.blocks import TestBlocks
from core.detection import Detection

from ..base import Exporter
from .. import FileExtension


@dataclass
class DetectionsExportData:
    names: list[str]
    test_blocks: list[TestBlocks]

    def zip(self):
        return zip(self.names, self.test_blocks)



class YOLOExporter(Exporter):

    @property
    def extension(self):
        return FileExtension.FOLDER
    
    @Exporter.folder_export
    def export(
            self,
            out_dir : Path,
            data : DetectionsExportData,
            imgs : list | Iterator | Generator = None,
            global_anchoring_ref : bool = False,
        ) -> bool:

        # If no data is provided, return False
        if len(data.names) == 0 or len(data.test_blocks) == 0:
            return False
        
        
        if global_anchoring_ref:
            status = self.__global_yolo_export(out_dir, data)
        else:
            status = self.__relative_yolo_export(out_dir, data)

        if imgs:
            fullsave = not global_anchoring_ref
            names = data.names
            blocks = data.test_blocks
            #TODO: Change this, dest coud be a single folder 
            dest = [out_dir for _ in names]
            self.save_images(dest, imgs, blocks, full_save=fullsave)

        return status


    def __global_yolo_export(
            self,
            out_dir : Path,
            data : DetectionsExportData,
        ) -> bool:

        for name, blocks in data.zip():
            # Make the image folder
            name = name.split('.')[0]

            text = ''
            
            for block in blocks.questions_blocks + [blocks.cpf_block]:
                # List all selected and unselected balls detections in a block
                detections : list[Detection] = block.container.get_by_type(
                    [
                        Detection.Type.SELECTED_BALL,
                        Detection.Type.UNSELECTED_BALL
                    ],
                    to_list=True
                )
                for detection in detections:
                    text += detection.to_yolo(global_anchoring_ref = True) + '\n'
        
            # Write the detections to the file
            with open(out_dir / f"{name}.txt", "w") as file:
                file.write(text)

        return True


    def __relative_yolo_export(
            self,
            out_dir : Path,
            data : DetectionsExportData,
        ) -> bool:

        # Main for loop
        for name, blocks in data.zip():

            # Make the image folder
            name = name.split('.')[0]
            
            # Write the detections to the file
            # First stage detections
            text = ''
            with open(out_dir / f"{name}.txt", "w") as file:
                text += blocks.cpf_block.root_detection.to_yolo() + '\n'
                for block in blocks.questions_blocks:
                    text += block.root_detection.to_yolo() + '\n'
                file.write(text)
            
            # Second stage detections
            for block in blocks.questions_blocks + [blocks.cpf_block]:
                text = ''

                # List all selected and unselected balls detections in a block
                detections : list[Detection] = block.container.get_by_type(
                    [
                        Detection.Type.SELECTED_BALL,
                        Detection.Type.UNSELECTED_BALL
                    ],
                    to_list=True
                )

                # Write the detections to the file
                block_name = name + \
                    f"_{block.root_detection.class_type.name.lower()}" + \
                    f"_{block.order:02}"

                with open(out_dir / f"{block_name}.txt", "w") as file:
                    for detection in detections:
                        text += detection.to_yolo() + '\n'
                    file.write(text)

        return True
