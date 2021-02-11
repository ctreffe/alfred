from pathlib import Path
from itertools import chain

from alfred3.data_manager import DataManager
from alfred3.export import Exporter, find_unique_name
import click


class Extractor:
    """
    Turns uncurated alfred data from json format into csv format.

    Args:
        in_path (str): Path to directory containing json files. If None
            (default), the current working directory will be used.
        out_path (str): Path to directory in which the output csv file
            will be place. If None (default), the current working
            directory will be used.
        delimiter (str): Delimiter to use in the resulting csv file.
            Defaults to ";"

    Examples:
        The extractor is used by calling one of its four methods. The
        following python code can be used to turn all alfred json
        datasets in the current working directory into a nice csv file.

        >>> from alfred3.export import Extractor
        >>> ex = Extractor()
        >>> ex.extract_exp_data()

    """

    def __init__(self, in_path: str = None, out_path: str = None, delimiter: str = ";"):
        self.in_path = Path(in_path) if in_path is not None else Path.cwd()
        self.out_path = Path(out_path) if out_path is not None else Path.cwd()
        self.delimiter = delimiter

    def extract_exp_data(self):
        """
        Extracts the main experiment data from json files in the
        Extractors *in_path*.

        Examples:
            Turn all alfred json datasets in the current working
            directory into a nice csv file.

            >>> from alfred3.cli.extract import Extractor
            >>> ex = Extractor()
            >>> ex.extract_exp_data()
        """
        data = list(
            DataManager.iterate_local_data(data_type=DataManager.EXP_DATA, directory=self.in_path)
        )
        fieldnames = DataManager.extract_ordered_fieldnames(data)
        alldata = [DataManager.flatten(d) for d in data]
        csvname = find_unique_name(directory=self.out_path, filename="exp_data.csv")
        Exporter.write(
            data=alldata,
            fieldnames=fieldnames,
            path=self.out_path / csvname,
            delimiter=self.delimiter,
        )

        return csvname

    def extract_unlinked_data(self):
        """
        Extracts unlinked data from json files in the Extractors
        *in_path*.

        Examples:
            Turn all alfred json datasets in the current working
            directory into a nice csv file.

            >>> from alfred3.cli.extract import Extractor
            >>> ex = Extractor()
            >>> ex.extract_unlinked_data()
        """
        existing_data = list(
            DataManager.iterate_local_data(
                data_type=DataManager.UNLINKED_DATA, directory=self.in_path
            )
        )
        data = [DataManager.flatten(d) for d in existing_data]
        fieldnames = DataManager.extract_fieldnames(data)
        csvname = find_unique_name(directory=self.out_path, filename="unlinked.csv")
        Exporter.write(
            data=data,
            fieldnames=fieldnames,
            path=self.out_path / csvname,
            delimiter=self.delimiter,
        )

        return csvname

    def extract_codebook(self, exp_version: str):
        """
        Extracts codebook data from json files in the Extractors
        *in_path*.

        Args:
            exp_version (str): Experiment version. Codebook data must
                be exported for specific experiment versions.

        Examples:
            Get a nice csv codebook for the json data in the current
            working directory.

            >>> from alfred3.cli.extract import Extractor
            >>> ex = Extractor()
            >>> ex.extract_codebook("1.0")
        """
        cursor = DataManager.iterate_local_data(
            data_type=DataManager.EXP_DATA, directory=self.in_path, exp_version=exp_version
        )

        cursor_unlinked = DataManager.iterate_local_data(
            data_type=DataManager.UNLINKED_DATA, directory=self.in_path, exp_version=exp_version
        )

        # extract individual codebooks for each experimen session
        cbdata_collection = []
        for entry in cursor:
            cb = DataManager.extract_codebook_data(entry)
            cbdata_collection.append(cb)
        for entry in cursor_unlinked:
            cb = DataManager.extract_codebook_data(entry)
            cbdata_collection.append(cb)

        # combine them to a single dictionary, overwriting old values
        # with newer ones
        data = {}
        for entry in cbdata_collection:
            data.update(entry)

        fieldnames = DataManager.extract_fieldnames(data.values())
        fieldnames = DataManager.sort_codebook_fieldnames(fieldnames)
        csvname = find_unique_name(directory=self.out_path, filename=f"codebook_{exp_version}.csv")
        Exporter.write(
            data=data.values(),
            fieldnames=fieldnames,
            path=self.out_path / csvname,
            delimiter=self.delimiter,
        )

        return csvname

    def extract_move_history(self):
        """
        Extracts movement data from json files in the Extractors
        *in_path*.

        Examples:
            Get a nice csv of movement data for json data in the
            current working directory.

            >>> from alfred3.cli.extract import Extractor
            >>> ex = Extractor()
            >>> ex.extract_move_history()
        """
        existing_data = DataManager.iterate_local_data(
            data_type=DataManager.EXP_DATA, directory=self.in_path
        )
        history = [d["exp_move_history"] for d in existing_data]
        fieldnames = DataManager.extract_fieldnames(chain(*history))
        history = chain(*history)
        csvname = find_unique_name(directory=self.out_path, filename="move_history.csv")
        Exporter.write(
            data=history,
            fieldnames=fieldnames,
            path=self.out_path / csvname,
            delimiter=self.delimiter,
        )

        return csvname


@click.command()
@click.option(
    "--dtype",
    default="exp_data",
    help="The data type to extratct form .json files. Can be 'exp_data', 'codebook', 'move_history', and 'unlinked_data'.",
    show_default=True,
)
@click.option(
    "--in_path",
    default=None,
    help="Path to directory containing json files. If None (default), the current working directory will be used.",
)
@click.option(
    "--out_path",
    default=None,
    help="Path to directory in which the output csv file will be place. If None (default), the current working directory will be used.",
)
@click.option(
    "--exp_version",
    default=None,
    help="The experiment version for which codebook data should be extracted. Only relevant for codebook data.",
)
@click.option(
    "--delimiter", default=";", help="Delimiter to use in the resulting csv file. Defaults to ';'"
)
def json_to_csv(dtype, in_path, out_path, exp_version, delimiter):
    extractor = Extractor(in_path=in_path, out_path=out_path, delimiter=delimiter)

    if dtype == "exp_data":
        csvname = extractor.extract_exp_data()

    elif dtype == "codebook":
        if exp_version is None:
            raise ValueError(
                "You must specify an experiment version for codebook extraction. See 'alfred3 json-to-csv --help' for more."
            )
        csvname = extractor.extract_codebook(exp_version=exp_version)

    elif dtype == "move_history":
        csvname = extractor.extract_move_history()

    elif dtype == "unlinked_data":
        csvname = extractor.extract_unlinked_data()

    else:
        msg = f"Value {dtype} for option '--dtype' is not valid. See 'alfred3 json-to-csv --help' for more."
        raise ValueError(msg)

    msg = (
        f"Data transformed to csv. File '{csvname}' was placed in directory '{extractor.out_path}'"
    )
    click.echo(msg)
