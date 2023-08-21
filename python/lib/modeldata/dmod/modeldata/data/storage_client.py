from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, List, Optional, TypeVar

DATA = TypeVar("DATA")
ITEM_ID = TypeVar("ITEM_ID")


class DataStorageClient(Generic[DATA, ITEM_ID], ABC):
    """
    Abstraction for working with data items and a storage backend that can contain them.

    Items stored within the data store should have an identifier of the generic ``ITEM_ID`` type.  This id uniquely
    isolates that particular item and describes "where" the item is located.

    Items stored within the data store contain data that can be accessed as objects of the generic ``DATA`` type.
    """

    @abstractmethod
    def delete_item(self, item_id: ITEM_ID, **kwargs) -> bool:
        """
        Delete the item with the given item identifier.

        Parameters
        ----------
        item_id : ITEM_ID
            The identifier for the item to delete.
        kwargs

        Returns
        -------
        bool
            Whether the delete was successful.
        """
        pass

    @abstractmethod
    def list_containers(self, **kwargs) -> List[str]:
        """
        List the names of all container entities that hold data items.

        A "container" will vary depending on implementation.  It may be a top-level base directory, a database table,
        an object store bucket, etc.

        Parameters
        ----------
        kwargs

        Returns
        -------
        List[str]
        """
        pass

    @abstractmethod
    def list_items(self, **kwargs) -> List[ITEM_ID]:
        """
        List the available, existing items this client can access.

        Parameters
        ----------
        kwargs

        Returns
        -------
        List[ITEM_ID]
            A list of item identifiers for all existing, accessible items.
        """
        pass

    @abstractmethod
    def read_item(self, item_id: ITEM_ID, **kwargs) -> DATA:
        """
        Read and return the data item.

        Parameters
        ----------
        item_id : ITEM_ID
            The unique item identifier.
        kwargs

        Returns
        -------
        DATA
            The data contained within the data item, as a ::class:`DATA`.
        """
        pass

    @abstractmethod
    def save_item(self, data: DATA, item_id: ITEM_ID, overwrite: bool = False, **kwargs) -> bool:
        """
        Save the provided data as an entire item with the given item identifier.

        Parameters
        ----------
        data : DATA
            The data to save as an item.
        item_id : ITEM_ID
            The identifier for the item to save, which implies a storage location.
        overwrite : bool
            Whether an existing item with the given identifier should be overwritten (``False`` by default).
        kwargs

        Returns
        -------
        bool
            Whether saving the item was successful.
        """
        pass


CLIENT = TypeVar("CLIENT", bound=DataStorageClient)


class FileSystemStorageClient(DataStorageClient[str, Path]):
    """
    General implementation dealing with raw string data within files in a file system under some base directory.

    For this type, items are files within the file system.
    """

    def __init__(self, base_directory: Optional[Path] = None, *args, **kwargs):
        self._base_dir: Path = base_directory if base_directory is not None else Path.root
        # TODO: sanity check base_dir

    def delete_item(self, item_id: Path, **kwargs) -> bool:
        """
        Delete the item with the given item identifier.

        Parameters
        ----------
        item_id : ITEM_ID
            The path to the item to delete.
        kwargs

        Keyword Args
        -------
        missing_ok : bool
            Optional param that, when set to ``True``, makes the function return ``True`` if the item to delete does not
            initially exist (effectively ``False`` if not provided).

        Returns
        -------
        bool
            Whether the delete was successful.
        """
        if not item_id.exists():
            return kwargs.get("missing_ok", False)
        elif item_id.is_file():
            try:
                item_id.unlink(missing_ok=kwargs.get("missing_ok", False))
            except Exception:
                return False
            return not item_id.exists()
        else:
            return False

    def list_containers(self, **kwargs) -> List[str]:
        """
        List the names of all container entities that hold data items.

        For this type, there is only one "container" : the top-level base directory.

        Parameters
        ----------
        kwargs

        Returns
        -------
        List[str]
        """
        return [str(self._base_dir)]

    def list_items(self, **kwargs) -> List[Path]:
        """
        List the available, existing files under this instance's base directory.

        Parameters
        ----------
        kwargs

        Returns
        -------
        List[Path]
            A list of item paths for all existing items under this instance's base directory.
        """
        return [f for f in self._base_dir.rglob('*') if f.is_file()]

    def read_item(self, item_id: Path, **kwargs) -> str:
        """
        Read and return the data item.

        Parameters
        ----------
        item_id : Path
            The path to the data item.
        kwargs

        Returns
        -------
        str
            The data contained within the data item, as a str.
        """
        return item_id.read_text()

    def save_item(self, data: str, item_id: Path, overwrite: bool = False, **kwargs) -> bool:
        """
        Save the provided data as an entire item with the given item identifier.

        Parameters
        ----------
        data : str
            The data to save as an item.
        item_id : Path
            The path at which to save the given data.
        overwrite : bool
            Whether an existing item/file at this path should be overwritten (``False`` by default).
        kwargs

        Returns
        -------
        bool
            Whether saving the item was successful.
        """
        return item_id.write_text(data) == len(data)


class StrAdaptorFileSystemClient(DataStorageClient[str, str]):
    """
    Adaptor for ::class:`FileSystemStorageClient` that handles item ids (and data) as strings.
    """

    def __init__(self, base_client: Optional[FileSystemStorageClient] = None, *args, **kwargs):
        """
        Initialize an instance.

        Instance can accept an already created base client object or create a new one. If creating a new one, it will
        pass ``args`` and ``kwargs`` to that object's ``__init__``, thus allowing for specifying ``base_directory`` if
        desired.

        Parameters
        ----------
        base_client : Optional[FileSystemStorageClient]
            Optional, already-initialized base storage client.
        args
        kwargs
        """
        if base_client is None:
            self._base_client: FileSystemStorageClient = FileSystemStorageClient(*args, **kwargs)
        else:
            self._base_client: FileSystemStorageClient = base_client

    def delete_item(self, item_id: str, **kwargs) -> bool:
        """
        Delete the item with the given item identifier.

        Parameters
        ----------
        item_id : str
            The path (as a string) to the item to delete.
        kwargs

        Keyword Args
        -------
        missing_ok : bool
            Optional param that, when set to ``True``, makes the function return ``True`` if the item to delete does not
            initially exist (effectively ``False`` if not provided).

        Returns
        -------
        bool
            Whether the delete was successful.
        """
        return self._base_client.delete_item(item_id=Path(item_id), **kwargs)

    def list_containers(self, **kwargs) -> List[str]:
        """
        List the names of all container entities that hold data items.

        For this type, there is only one "container" : the top-level base directory.

        Parameters
        ----------
        kwargs

        Returns
        -------
        List[str]
        """
        return self._base_client.list_containers(**kwargs)

    def list_items(self, **kwargs) -> List[str]:
        """
        List the available, existing items under this instance's base directory.

        Parameters
        ----------
        kwargs

        Returns
        -------
        List[str]
            A list of item identifiers for all existingitems under this instance's base directory.
        """
        return [str(i) for i in self._base_client.list_items(**kwargs)]

    def read_item(self, item_id: str, **kwargs) -> str:
        """
        Read and return the data item.

        Parameters
        ----------
        item_id : str
            The path to the item, represented as a ``str``.
        kwargs

        Returns
        -------
        str
            The data contained within the data item, as a str.
        """
        return self._base_client.read_item(item_id=Path(item_id), **kwargs)

    def save_item(self, data: str, item_id: str, overwrite: bool = False, **kwargs) -> bool:
        """
        Save the provided data as an entire item with the given item identifier.

        Parameters
        ----------
        data : str
            The data to save as an item.
        item_id : str
            The identifier for the item to save, which implies a storage location.
        overwrite : bool
            Whether an existing item with the given identifier should be overwritten (``False`` by default).
        kwargs

        Returns
        -------
        bool
            Whether saving the item was successful.
        """
        return self._base_client.save_item(data=data, item_id=Path(item_id), overwrite=overwrite, **kwargs)


# TODO: implement MinIOStorageClient