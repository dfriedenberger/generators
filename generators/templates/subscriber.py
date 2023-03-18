from cyclonedds.domain import DomainParticipant
from cyclonedds.core import Qos, Policy
from cyclonedds.sub import DataReader
from cyclonedds.pub import DataWriter
from cyclonedds.topic import Topic


from src.messages import ExampleMessage, ExampleResult
from src.mocks import ProxyMock

dp = DomainParticipant()
tp1 = Topic(dp, "ExampleTopic", ExampleMessage, qos=Qos(Policy.Reliability.Reliable(0)))
dr1 = DataReader(dp, tp1)

tp2 = Topic(dp, "ExampleTopic2", ExampleResult, qos=Qos(Policy.Reliability.Reliable(0)))
dw2 = DataWriter(dp, tp2)


def apply(params):
    print("callback",params)
    message = ExampleResult(name="facade", params=params[0])
    dw2.write(message)




proxy = ProxyMock()
proxy.set_callback(apply)

while True:
    for message in dr1.take(10):
        print("Recv ", message)
        proxy.apply(message.params)
