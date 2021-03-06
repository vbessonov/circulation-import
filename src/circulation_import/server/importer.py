import logging
import subprocess
from typing import List

from circulation_import.server.configuration import ImporterConfiguration
from circulation_import.storage.model import CollectionMetadata
from circulation_import.storage.model import ProcessingStatus


class Importer:
    def __init__(self, configuration: ImporterConfiguration) -> None:
        self._configuration: ImporterConfiguration = configuration
        self._logger = logging.getLogger(__name__)

    def _create_parameters(
        self, collection_metadata: CollectionMetadata, new_book_directory: str
    ) -> List:
        parameters = [self._configuration.import_script_command]

        parameters.extend(
            [
                "--collection-name",
                f"\"{self._configuration.collection_name}\"",
                "--collection-type",
                self._configuration.collection_type,
                "--data-source-name",
                f"\"{self._configuration.data_source_name}\"",
                "--metadata-format",
                f"\"{collection_metadata.metadata_format}\"",
                "--metadata-file",
                f"\"{collection_metadata.metadata_file}\"",
                "--ebook-directory",
                f"\"{new_book_directory}\"",
                "--cover-directory",
                f"\"{collection_metadata.covers_directory}\"",
                "--rights-uri",
                self._configuration.rights_uri,
            ]
        )

        return parameters

    def run(self, collection_metadata: CollectionMetadata) -> None:
        self._logger.info(f"Started importing {collection_metadata}")

        parameters = self._create_parameters(
            collection_metadata, collection_metadata.books_directory
        )

        self._logger.debug(f"directory_import's parameters: {parameters}")

        try:
            output = subprocess.check_output(
                " ".join(parameters), shell=True, executable="/bin/bash"
            )

            self._logger.debug(f"Output of directory_import: {output}")

            for book_metadata in collection_metadata.books:
                book_metadata.status = ProcessingStatus.PROCESSED.value
                book_metadata.error = None
        except Exception:
            self._logger.exception(
                "An unexpected exception occurred during running the directory_import script"
            )

            for book_metadata in collection_metadata.books:
                book_metadata.status = ProcessingStatus.FAILED.value
                book_metadata.error = "bin/directory_import script failed"

        self._logger.info(f"Finished importing {collection_metadata}")
