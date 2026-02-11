import os
import shutil
from os.path import exists
from pathlib import Path

import pyzipper
from pyzipper import zipfile

from os import makedirs, path


class ArchiveBuilder:

    def __init__(self):

        self._encryption_strength = 256 #Default encryption strength. Supporting AES 128, 192, and 256
        self._extension = ".zip" #archive format
        self._compression_strength = pyzipper.ZIP_DEFLATED #Allowed values ZIP_STORED = 0; ZIP_DEFLATED = 8;
                                                                        # ZIP_BZIP2 = 12; ZIP_LZMA = 14
        self._password =  "" # By default, it is an empty string. If so. No encryption is done
        self._sources = []  # The list of files and directories to be archived
        self._archive_file_name = "archive" # The name of the archive file
        self._output_path = path.dirname(path.abspath(__file__)) + "/output/"
        self._purge_enabled = True if __name__ != "__main__"  else False # purge is disabled for testing purposes
        self._purge_output()


    def _purge_output(self):
        if self._purge_enabled:
            shutil.rmtree(self._output_path, ignore_errors=True)
            makedirs(self._output_path, exist_ok=True)


    def set_encryption_strength(self, encryption_strength):
        self._encryption_strength = encryption_strength


    def add_source(self, source) -> object:
        self._sources.append(source)
        return self


    def set_password(self, password: str = ""):
        self._password = password


    def set_extension(self, extension: str = ".zip"):
        self._extension = extension


    def set_compression_strength(self, compression_strength = pyzipper.ZIP_DEFLATED):
        self._compression_strength = compression_strength


    def set_archive_file_name(self, archive_file_name: str = "archive"):
        self._archive_file_name = archive_file_name


    def archive(self):
        self._purge_output()
        #Check at least was added
        if len(self._sources) == 0:
            message = "No files to archive. Please attach sources"
            print(message)
        else:
            archive_file = self._output_path + self._archive_file_name + self._extension
            #check if password is set. If it's an empty string call simple archiver.
            if self._password == "":
                self._simple_archiver(archive_file)
            else:
                self._encrypted_archiver(archive_file)


    def _simple_archiver(self, arc_name: str):
        with zipfile.ZipFile(arc_name, 'w') as arc:
            for source in self._sources:
                arc.write(source)


    def _encrypted_archiver(self, arc_name: str):
        pwd = self._password.encode("utf-8")

        with pyzipper.AESZipFile(
                arc_name,
                "w",
                compression=self._compression_strength
        ) as arc:
            arc.setencryption(pyzipper.WZ_AES, nbits=self._encryption_strength)
            arc.setpassword(pwd)
            arc.writestr('test.txt', "What ever you do, don't tell anyone!")
            for src in self._sources:
                src_path = Path(src)
                arc.write(src, arcname=src_path.name)  # store clean name in zip



    def extract_all(self, arc_path: str, password: str = "") -> Path:
        arc = Path(arc_path)

        if not arc.exists():
            raise FileNotFoundError(f"Archive not found: {arc}")

        if not zipfile.is_zipfile(arc):
            raise ValueError(f"{arc} is not a valid ZIP or is unsupported")

        dest_dir = Path(self._output_path) / arc.stem
        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            with pyzipper.AESZipFile(arc, "r") as zf:
                if password not in ("", None):
                    zf.pwd = password.encode("utf-8")
                zf.extractall(dest_dir)
        except RuntimeError as e:
            raise RuntimeError(f"Extraction failed (password/encryption issue?): {e}") from e
        except Exception as e:
            raise RuntimeError(f"Extraction failed: {e}") from e

        print(f"Extracted to: {dest_dir.resolve()}")
        return dest_dir

if __name__ == "__main__":
    # Test compression and decompression
    encryption_strengths = [None, 128,192,256]
    # Allowed values ZIP_STORED = 0; ZIP_DEFLATED = 8;
    # ZIP_BZIP2 = 12; ZIP_LZMA = 14
    compression_methods = [pyzipper.ZIP_STORED, pyzipper.ZIP_DEFLATED, pyzipper.ZIP_LZMA, pyzipper.ZIP_BZIP2]
    for es in encryption_strengths:
        arc_pwd = "123456"
        if es is None:
            arc_pwd = ""
        for c in compression_methods:
            archive_builder = ArchiveBuilder()
            archive_builder.add_source("text.txt")
            archive_builder.add_source("text2.txt")
            archive_builder.set_password(password=arc_pwd)
            archive_builder.set_compression_strength(c)
            str1= "STORED" if c == 0 else "DEFLATED" if c == 8 else "BZIP2" if c == 12 else "LZMA"
            str2= "-NONE" if es is None else str(es)
            print(f"{str1}, {str2}")
            archive_builder.set_archive_file_name(str1 + str2)
            archive_builder.archive()

    archive_builder = ArchiveBuilder()
    for file_name in os.listdir(archive_builder._output_path):
        if "NONE" in file_name:
            archive_builder.extract_all(archive_builder._output_path + file_name)
        else:
            archive_builder.extract_all(archive_builder._output_path + file_name, "123456")
