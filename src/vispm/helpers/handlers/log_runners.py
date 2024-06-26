
from ..data.log_data import SequenceData
from ..metaclasses.pm4py import EventLog,Trace,Event

from typing import List, Any

class SequenceDataExtractor():
    """
    Given a event log, this class extracts the minimum amount of data needed for visualisation. Should be used a one-shot.\n
    Assumptions:\n
    \tThe given event log has been sorted by starting event timestamp.
    """

    TIME_ATTR = "time:timestamp"
    LABEL_ATTR = "concept:name"
    LIFE_ATTR = "lifecycle:transition"
    RESOURCE_ATTR = "org:resource"

    DEFAULT = "MISSING"

    def __init__(self) -> None:
        self._errored_keys = dict() 

    def __call__(self, event_log:EventLog,start_time=None) -> List[SequenceData]:
        """Begins extracting SequenceData from an EventLog"""
        return self._convert_log(event_log,start_time=start_time)

    def _extract_xes_key(self, key:str, event:Event,default:Any) -> Any:
        try :
            from pmkoalas.complex import ComplexEvent
            if isinstance(event, ComplexEvent) and key == self.LABEL_ATTR:
                return event.activity()
            else:
                try :
                    return event[key]
                except:
                    if not key in self._errored_keys.keys():
                        print(f"[{self.__class__.__name__}] Unable to extract XES key on event : missing {key}. Plotting may be affected.")
                        self._errored_keys[key] = event
                    return default
        except:
            try :
                return event[key]
            except:
                if not key in self._errored_keys.keys():
                    print(f"[{self.__class__.__name__}] Unable to extract XES key on event : missing {key}. Plotting may be affected.")
                    self._errored_keys[key] = event
                return default

    def _convert_trace(self,trace:Trace, startingTime:float) -> List[SequenceData]:
        timepoints = [] 
        for event in trace:
            time = self._extract_xes_key(self.TIME_ATTR, event, None)#event[self.TIME_ATTR].timestamp() - startingTime
            if time != None:
                weekday = time.weekday()
                monthday = time.day
                time = time.timestamp() - startingTime
            else:
                weekday = -1
                monthday = -1 
                time = 0.0
            label = self._extract_xes_key(self.LABEL_ATTR, event, self.DEFAULT)
            lifecycle = self._extract_xes_key(self.LIFE_ATTR, event, self.DEFAULT)
            resource = str(self._extract_xes_key(self.RESOURCE_ATTR, event , self.DEFAULT))
            data = SequenceData(time,weekday,monthday,label,lifecycle,resource)
            timepoints.append(data)
        timepoints = sorted(timepoints, key=lambda x: x.time)
        return timepoints

    def _convert_log(self,log:EventLog,start_time=None) -> List[List[SequenceData]]:
        log_sequences = []
        try :
            from pmkoalas.complex import ComplexEventLog
            if isinstance(log, ComplexEventLog):
                if start_time != None:
                    startingTime = start_time.timestamp()
                else:
                    startingTime = None
                    for variant, traces in log:
                        for trace in traces:
                            time = self._extract_xes_key(self.TIME_ATTR, trace[0], None)
                            if time == None:
                                continue
                            elif startingTime == None and time != None:
                                startingTime = time 
                            else:
                                if (time < startingTime):
                                    startingTime = time
                for variant, traces in log:
                        for trace in traces:
                            log_sequences.append(self._convert_trace(trace,startingTime.timestamp()))
            else:
                raise ValueError("not a pmkoalas data structure")
        except:
            if start_time == None:
                startingTime = log[0][0][self.TIME_ATTR].timestamp()
            else:
                startingTime = start_time.timestamp()
            for trace in log:
                log_sequences.append(self._convert_trace(trace,startingTime))
        log_sequences = sorted(log_sequences,key=lambda x: x[0].time if len(x)> 0 else startingTime)
        return log_sequences