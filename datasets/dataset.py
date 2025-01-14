import os
import pickle
import os.path as osp
import torch.utils.data as tordata
import json

from torch.utils.data import dataset
from util_tools import get_msg_mgr


class InferenceDataSet(tordata.Dataset):
    def __init__(self, dataset_root, gallary = True, cache = False):
        self.__dataset_parser(dataset_root, gallary)
        self.cache = cache
        # seq_info: label type views [paths ..]
        self.label_list = [seq_info[0] for seq_info in self.seqs_info]
        self.label_set = sorted(list(set(self.label_list)))
        self.seqs_data = [None] * len(self)
        if self.cache:
            self.__load_all_data()

    def __len__(self):
        return len(self.seqs_info)

    def __loader__(self, paths):
        paths = sorted(paths)
        data_list = []
        for pth in paths:
            if pth.endswith('.pkl'):
                with open(pth, 'rb') as f:
                    _ = pickle.load(f)
                f.close()
            else:
                raise ValueError('- Loader - just support .pkl !!!')
            # if len(_) >= 200:
            #     _ = _[:200]
            data_list.append(_)
        for data in data_list:
            if len(data) != len(data_list[0]):
                raise AssertionError

        return data_list

    def __getitem__(self, idx):
        if not self.cache:
            data_list = self.__loader__(self.seqs_info[idx][-1])
        elif self.seqs_data[idx] is None:
            data_list = self.__loader__(self.seqs_info[idx][-1])
            self.seqs_data[idx] = data_list
        else:
            data_list = self.seqs_data[idx]
        seq_info = self.seqs_info[idx]
        return data_list, seq_info

    def __load_all_data(self):
        for idx in range(len(self)):
            self.__getitem__(idx)

    #type: gallary or probe
    def __dataset_parser(self, dataset_root, gallary = True): 
        
        if gallary:
            data_path = os.path.join(dataset_root, "gallary")
        else:
            data_path = os.path.join(dataset_root, "probe")

        labels = os.listdir(data_path)

        msg_mgr = get_msg_mgr()

        def log_pid_list(pid_list):
            if len(pid_list) >= 3:
                msg_mgr.log_info('[%s, %s, ..., %s]' %
                                 (pid_list[0], pid_list[1], pid_list[-1]))
            else:
                msg_mgr.log_info(pid_list)

        if gallary:
            msg_mgr.log_info("-------- Gallary Pid List --------")
            log_pid_list(labels)
        else:
            msg_mgr.log_info("-------- Probe Pid List --------")
            log_pid_list(labels)

        def get_seqs_info_list(data_path, label_set):
            seqs_info_list = []
            for label in label_set:
                seq_dir = osp.join(data_path, label)
                seqs_info_list.append([label, seq_dir])
            return seqs_info_list

        def get_seqs_info_list(data_path, label_set):
            seqs_info_list = []
            for lab in label_set:
                typ = None
                vie = None
                seq_info = [lab, typ, vie]
                seq_path = osp.join(data_path, lab)
                seq_dirs = sorted(os.listdir(seq_path))
                if seq_dirs != []:
                    seq_dirs = [osp.join(seq_path, dir)
                                for dir in seq_dirs]
                    seqs_info_list.append([*seq_info, seq_dirs])
                else:
                    msg_mgr.log_debug('Find no .pkl file in %s-%s-%s.'%(lab, typ, vie))
            return seqs_info_list

        self.seqs_info = get_seqs_info_list(data_path, labels)

class DataSet(tordata.Dataset):
    def __init__(self, dataset_root, training, dataset_partition, cache = False):
        """
            seqs_info: the list with each element indicating 
                            a certain gait sequence presented as [label, type, view, paths];
        """
        self.__dataset_parser(dataset_root, training, dataset_partition)
        self.cache = cache
        # seq_info: label type views [paths ..]
        self.label_list = [seq_info[0] for seq_info in self.seqs_info]
        self.types_list = [seq_info[1] for seq_info in self.seqs_info]
        self.views_list = [seq_info[2] for seq_info in self.seqs_info]

        self.label_set = sorted(list(set(self.label_list)))
        self.types_set = sorted(list(set(self.types_list)))
        self.views_set = sorted(list(set(self.views_list)))
        self.seqs_data = [None] * len(self)
        # indices_dict 相同label的 seqs_info的索引
        self.indices_dict = {label: [] for label in self.label_set}
        for i, seq_info in enumerate(self.seqs_info):
            self.indices_dict[seq_info[0]].append(i)
        if self.cache:
            self.__load_all_data()

    def __len__(self):
        return len(self.seqs_info)

    def __loader__(self, paths):
        paths = sorted(paths)
        data_list = []
        for pth in paths:
            if pth.endswith('.pkl'):
                with open(pth, 'rb') as f:
                    _ = pickle.load(f)
                f.close()
            else:
                raise ValueError('- Loader - just support .pkl !!!')
            # if len(_) >= 200:
            #     _ = _[:200]
            data_list.append(_)
        for data in data_list:
            if len(data) != len(data_list[0]):
                raise AssertionError

        return data_list

    def __getitem__(self, idx):
        if not self.cache:
            data_list = self.__loader__(self.seqs_info[idx][-1])
        elif self.seqs_data[idx] is None:
            data_list = self.__loader__(self.seqs_info[idx][-1])
            self.seqs_data[idx] = data_list
        else:
            data_list = self.seqs_data[idx]
        seq_info = self.seqs_info[idx]
        return data_list, seq_info

    def __load_all_data(self):
        for idx in range(len(self)):
            self.__getitem__(idx)

    def __dataset_parser(self, dataset_root, training, dataset_partition):
      
        data_in_use = None

        with open(dataset_partition, "rb") as f:
            partition = json.load(f)
        train_set = partition["TRAIN_SET"]
        test_set = partition["TEST_SET"]
        label_list = os.listdir(dataset_root)
        train_set = [label for label in train_set if label in label_list]
        test_set = [label for label in test_set if label in label_list]
        miss_pids = [label for label in label_list if label not in (
            train_set + test_set)]
        msg_mgr = get_msg_mgr()

        def log_pid_list(pid_list):
            if len(pid_list) >= 3:
                msg_mgr.log_info('[%s, %s, ..., %s]' %
                                 (pid_list[0], pid_list[1], pid_list[-1]))
            else:
                msg_mgr.log_info(pid_list)

        if len(miss_pids) > 0:
            msg_mgr.log_debug('-------- Miss Pid List --------')
            msg_mgr.log_debug(miss_pids)
        if training:
            msg_mgr.log_info("-------- Train Pid List --------")
            log_pid_list(train_set)
        else:
            msg_mgr.log_info("-------- Test Pid List --------")
            log_pid_list(test_set)

        def get_seqs_info_list(label_set):
            seqs_info_list = []
            for lab in label_set:
                for typ in sorted(os.listdir(osp.join(dataset_root, lab))):
                    for vie in sorted(os.listdir(osp.join(dataset_root, lab, typ))):
                        seq_info = [lab, typ, vie]
                        seq_path = osp.join(dataset_root, *seq_info)
                        seq_dirs = sorted(os.listdir(seq_path))
                        if seq_dirs != []:
                            seq_dirs = [osp.join(seq_path, dir)
                                        for dir in seq_dirs]
                            if data_in_use is not None:
                                seq_dirs = [dir for dir, use_bl in zip(
                                    seq_dirs, data_in_use) if use_bl]
                            seqs_info_list.append([*seq_info, seq_dirs])
                        else:
                            msg_mgr.log_debug('Find no .pkl file in %s-%s-%s.'%(lab, typ, vie))
            return seqs_info_list

        self.seqs_info = get_seqs_info_list(
            train_set) if training else get_seqs_info_list(test_set)
