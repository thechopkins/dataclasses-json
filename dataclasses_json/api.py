import abc
import json
from typing import (Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar,
                    Union)

from dataclasses_json.cfg import config, LetterCase  # noqa: F401
from dataclasses_json.core import (Json, _ExtendedEncoder, _asdict,
                                   _decode_dataclass)
from dataclasses_json.undefined import Undefined
from dataclasses_json.utils import (_handle_undefined_parameters_safe,
                                    _undefined_parameter_action_safe)

A = TypeVar('A', bound="DataClassJsonMixin")
B = TypeVar('B')
C = TypeVar('C')
Fields = List[Tuple[str, Any]]


class DataClassJsonMixin(abc.ABC):
    """
    DataClassJsonMixin is an ABC that functions as a Mixin.

    As with other ABCs, it should not be instantiated directly.
    """
    dataclass_json_config = None

    def to_json(self,
                *,
                skipkeys: bool = False,
                ensure_ascii: bool = True,
                check_circular: bool = True,
                allow_nan: bool = True,
                indent: Optional[Union[int, str]] = None,
                separators: Tuple[str, str] = None,
                default: Callable = None,
                sort_keys: bool = False,
                **kw) -> str:
        return json.dumps(self.to_dict(encode_json=False),
                          cls=_ExtendedEncoder,
                          skipkeys=skipkeys,
                          ensure_ascii=ensure_ascii,
                          check_circular=check_circular,
                          allow_nan=allow_nan,
                          indent=indent,
                          separators=separators,
                          default=default,
                          sort_keys=sort_keys,
                          **kw)

    @classmethod
    def from_json(cls: Type[A],
                  s: Any,
                  *,
                  parse_float=None,
                  parse_int=None,
                  parse_constant=None,
                  infer_missing=False,
                  **kw) -> A:
        kvs = json.loads(s,
                         parse_float=parse_float,
                         parse_int=parse_int,
                         parse_constant=parse_constant,
                         **kw)
        return cls.from_dict(kvs, infer_missing=infer_missing)

    @classmethod
    def from_dict(cls: Type[A],
                  kvs: Json,
                  *,
                  infer_missing=False) -> A:
        return _decode_dataclass(cls, kvs, infer_missing)

    def to_dict(self, encode_json=False) -> Dict[str, Json]:
        return _asdict(self, encode_json=encode_json)

def dataclass_json(_cls=None, *, letter_case=None,
                   undefined: Optional[Union[str, Undefined]] = None):
    """
    Based on the code in the `dataclasses` module to handle optional-parens
    decorators. See example below:

    @dataclass_json
    @dataclass_json(letter_case=LetterCase.CAMEL)
    class Example:
        ...
    """

    def wrap(cls):
        return _process_class(cls, letter_case, undefined)

    if _cls is None:
        return wrap
    return wrap(_cls)


def _process_class(cls, letter_case, undefined):
    if letter_case is not None or undefined is not None:
        cls.dataclass_json_config = config(letter_case=letter_case,
                                           undefined=undefined)[
            'dataclasses_json']

    cls.to_json = DataClassJsonMixin.to_json
    # unwrap and rewrap classmethod to tag it to cls rather than the literal
    # DataClassJsonMixin ABC
    cls.from_json = classmethod(DataClassJsonMixin.from_json.__func__)
    cls.to_dict = DataClassJsonMixin.to_dict
    cls.from_dict = classmethod(DataClassJsonMixin.from_dict.__func__)

    cls.__init__ = _handle_undefined_parameters_safe(cls, kvs=(), usage="init")
    # register cls as a virtual subclass of DataClassJsonMixin
    DataClassJsonMixin.register(cls)
    return cls
