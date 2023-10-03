# Cycle class constructed from cycle files in Azure blob


class Cycle:
    def __init__(self, duration, cycle_data) -> None:
        self.id = cycle_data["device_cycle_id"]
        self.type = cycle_data["cycle_type"]
        self.duration = duration

        self.analog_set = set(
            ["RRTD", "FXRES", "GRTD", "JRTD", "TSENS", "WRTD", "CRTD", "CPRES"]
        )
        self.digital_set = set(
            [
                "DLS",
                "DOORASW2",
                "DOORA_CLSD",
                "DOORA_PLK",
                "DOORA_SEAL",
                "DOORB_PLK",
                "DOORB_SEAL",
                "NEUT1_SW",
                "NEUT2_SW",
                "NO_FLOOD",
                "S01",
                "S02",
                "S03",
                "S04",
                "S07",
                "S09",
                "S35",
                "S37",
                "S40",
                "S43",
            ]
        )

        # build a digital dict and remove unnecessary digital data
        self.digital_dict = {x: None for x in self.digital_set}
        for digital in cycle_data["ioevents"]:
            self.digital_dict[digital["name"]] = digital
            del digital["PID"]
            del digital["desc"]
            del digital["name"]

        # remove unnecessary analog data
        for i, ts in enumerate(cycle_data["analog"]):
            for j, channel in enumerate(ts["values"]):
                del channel["channelName"]
                del channel["channelId"]
                del channel["unit"]
                # replace buggy 99999 values with the average of prev val and next val
                if channel["value"] == "99999":
                    prev = False
                    next = False
                    if i != 0:
                        prev = cycle_data["analog"][i - 1]["values"][j]["value"]
                    if i != len(cycle_data["analog"]) - 1:
                        next = cycle_data["analog"][i + 1]["values"][j]["value"]
                    if prev != False and next != False:
                        channel["value"] = str((float(prev) + float(next)) / 2)
                    elif not prev:
                        channel["value"] = next
                    elif not next:
                        channel["value"] = prev

        self.analog = cycle_data["analog"]

    # number of activations of digital actuations in a cycle
    def act_count(self) -> dict:
        count = {x: 0 for x in self.digital_dict}
        for digital_name, data in self.digital_dict.items():
            if data != None:
                for value in data["values"]:
                    if int(value["status"]) == 1:
                        count[digital_name] += 1
        return count

        # if getattr(self, digital_name) == None:
        #     return 0
        # data = getattr(self, digital_name)['values']
        # count = 0
        # for status in data:
        #     if status['status'] == '1':
        #         count += 1
        # return count

    # if digital starts with status 1
    def digital_init(self) -> dict:
        init = {x: 0 for x in self.digital_dict}
        for digital_name, data in self.digital_dict.items():
            if data != None:
                init[digital_name] = int(not data["values"][0]["status"])
        return init

    # if digital ends with status 1
    def digital_end(self) -> dict:
        end = {x: 0 for x in self.digital_dict}
        for digital_name, data in self.digital_dict.items():
            if data != None:
                end[digital_name] = int(data["values"][-1]["status"])
        return end

    # returns relative time of first activation. 0.5 means first activation
    # took place 50% into the cycle. 0 means never activated
    def first_act(self) -> dict:
        first = {x: 0 for x in self.digital_dict}
        for digital_name, data in self.digital_dict.items():
            if data != None:
                first[digital_name] = float(data["values"][0]["ts"]) / self.duration
        return first

    # compute corresponding features and return a list of length
    # 3 (slope, avg, stdv) * 25 (1/25 of a cycle) * # of channels
    # more specifically:
    # ch1avg_1, ch1avg_2, ..., ch1abg_25,
    # ch1stdv_1, ch1stdv_2, ..., ch1stdv_25,
    # ch1slp_1, ch1slp_2, ..., ch1slp_25,
    # ch2avg_1, ch2avg_2, ..., ch2avg_25,
    # ch2stdv_1, ch2stdv_2, ..., ch2stdv_25,
    # ch2slp_1, ch2slp_2, ..., ch2slp_25,
    # ch3avg_1, ch3avg_2, ..., ch3avg_25,
    # ch3stdv_1, ch3stdv_2, ..., ch3stdv_25,
    # ch3slp_1, ch3slp_2, ..., ch3slp_25,
    # ...

    def analog_adv(self) -> list:
        output = [0] * 25 * 3 * len(self.analog_set)
        step = int(duration / 25)
        data = self.analog
        split = {x: data[x : x + step] for x in range(24)}
        split[24] = data[int(split[23]["ts"]) :]
        for num, sp in split.items():
            avg, stdv, slope = avg_stdv_slope(sp)

    def avg_stdv_slope(self, segment: list) -> dict:
        stdv, slope = {x: None for x in self.analog_set}, {
            x: None for x in self.analog_set
        }
        init = {var: [] for var in self.analog_set}
        for ts in segment:
            code = ts["channelCode"]
            value = float(ts["value"])
            # skip buggy values
            if value != 99999.0:
                init[code].append(float(ts["value"]))

        avg = {x: np.average(y) for x, y in init.items()}
        stdv = {x: np.std(y) for x, y in init.items()}
        slope = {x: (y[-1] - y[0]) / (len(y) - 1) for x, y in init.items()}

        return avg, stdv, slope

    # count the number of local maxima and minima in analog reading
    # start and end also count as minima/maxima
    # I use strict greater than and less than, [1,2,3] would return (1,1) bc it counts the first element
    # as a pit and the last element as a peak
    def count_p(self, a):
        j = 0
        pit = 0
        peak = 0
        lt = True
        gt = True
        while j < len(a):
            if j == len(a) - 1 and lt and gt:
                return 0, 0
            elif j == len(a) - 1 and lt:
                peak += 1
                return peak, pit
            elif j == len(a) - 1 and gt:
                pit += 1
                return peak, pit
            for l in range(j + 1, len(a)):
                if a[j] < a[l] and gt:
                    pit += 1
                    gt = False
                    lt = True
                    j = l
                    break
                elif a[j] > a[l] and lt:
                    peak += 1
                    gt = True
                    lt = False
                    j = l
                    break
            j = l

    def analog_count_peak_pit(self):
        val_lists = {x: [] for x in self.analog_set}
        data = self.analog
        for i in range(len(data)):
            ts = data[i]
            v = ts["values"]
            for j in range(len(v)):
                val_lists[v[j]["channelCode"]].append(float(v[j]["value"]))
        peak, pit = {}, {}
        for channel, val_list in val_lists.items():
            peak_i, pit_i = self.count_p(val_list)
            peak[channel] = peak_i
            pit[channel] = pit_i
        return peak, pit
