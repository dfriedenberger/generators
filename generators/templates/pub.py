from cyclonedds.domain import DomainParticipant
from cyclonedds.core import Qos, Policy
from cyclonedds.pub import DataWriter
from cyclonedds.sub import DataReader
from cyclonedds.topic import Topic
import time


from src.Transcribed import Transcribed

dp = DomainParticipant()

topicTranscribed = Topic(dp, "TranscribedTopic", Transcribed, qos=Qos(Policy.Reliability.Reliable(0)))
dwTranscribed = DataWriter(dp, topicTranscribed)


test_msg = "Hello World"
message = Transcribed(length=len(test_msg),text=test_msg)
dwTranscribed.write_dispose(message)

