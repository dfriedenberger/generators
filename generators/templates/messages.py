from dataclasses import dataclass
from cyclonedds.idl import IdlStruct
from cyclonedds.idl.annotations import key


@dataclass
class ExampleMessage(IdlStruct, typename="ExampleMessage"):
    name: str
    key("name")
    params: str
    

@dataclass
class ExampleResult(IdlStruct, typename="ExampleResult"):
    name: str
    key("name")
    params: str