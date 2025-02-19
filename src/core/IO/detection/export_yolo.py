from typing import Iterator, Generator
from dataclasses import dataclass
from pathlib import Path

from core.definitions.blocks import TestBlocks
from core.detection import Detection

from .. import (
    Exporter,
    FileExtension,
    ROOT_PATH
)


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
            fullpath : Path,
            data : DetectionsExportData,
            imgs : list | Iterator | Generator = None
        ) -> bool:

        # If no data is provided, return False
        if len(data.names) == 0 or len(data.test_blocks) == 0:
            return False

        # Main for loop
        for name, blocks in data.zip():
            
            # Check if the blocks are None
            if not blocks:
                continue

            # Make the image folder
            name = name.split('.')[0]
            output_folder = fullpath / name
            output_folder.mkdir(parents=True)
            
            # Write the detections to the file
            # First stage detections
            text = ''
            with open(output_folder / f"{name}.txt", "w") as file:
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
                with open(output_folder / f"{block_name}.txt", "w") as file:
                    for detection in detections:
                        text += detection.to_yolo() + '\n'
                    file.write(text)

        if imgs:
            names = data.names
            blockss = data.test_blocks
            dest = [fullpath / name.split('.')[0] for name in names]
            self.save_images(dest, imgs, blockss)


        return True


