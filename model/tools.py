import sys, os, random, json, uuid, time, argparse, logging, logging.config
import numpy as np, sys, os, random, pdb, json, uuid, time, argparse
from random import randint
from collections import defaultdict as ddict, Counter
from ordered_set import OrderedSet
from pprint import pprint

# PyTorch related imports
import torch
from torch.nn import functional as F
from torch.nn.parameter import Parameter
from torch.nn.init import xavier_normal_, xavier_uniform_
from torch.nn import Parameter as Param
from torch.utils.data import DataLoader
from torch_scatter import scatter_add

from torch.fft import irfft2		#解决不同版本torch没有irfft
from torch.fft import rfft2
def rfft(x, d):
    t = rfft2(x, dim = (-d))
    return torch.stack((t.real, t.imag), -1)
def irfft(x, d, signal_sizes):
    return irfft2(torch.complex(x[:,:,0], x[:,:,1]), s = signal_sizes, dim = (-d))


np.set_printoptions(precision=4)

def set_gpu(gpus):
	os.environ["CUDA_DEVICE_ORDER"]    = "PCI_BUS_ID"	# 按照PCI_BUS_ID顺序从0开始排列GPU设备 
	os.environ["CUDA_VISIBLE_DEVICES"] = gpus	 #设置当前使用的GPU设备号
	
	#设置使用cpu
	# os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
	# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


def get_logger(name, log_dir, config_dir):
	config_dict = json.load(open( config_dir + 'log_config.json'))
	if not os.path.isdir(log_dir):
    	os.makedirs(log_dir)
	config_dict['handlers']['file_handler']['filename'] = log_dir + name.replace(':', '-')
	logging.config.dictConfig(config_dict)
	logger = logging.getLogger(name)

	std_out_format = '%(asctime)s - [%(levelname)s] - %(message)s'
	consoleHandler = logging.StreamHandler(sys.stdout)
	consoleHandler.setFormatter(logging.Formatter(std_out_format))
	logger.addHandler(consoleHandler)

	return logger

def get_combined_results(left_results, right_results):
	results = {}
	count   = float(left_results['count'])

	results['left_mr']	= round(left_results ['mr'] /count, 5)
	results['left_mrr']	= round(left_results ['mrr']/count, 5)
	results['right_mr']	= round(right_results['mr'] /count, 5)
	results['right_mrr']	= round(right_results['mrr']/count, 5)
	results['mr']		= round((left_results['mr']  + right_results['mr']) /(2*count), 5)
	results['mrr']		= round((left_results['mrr'] + right_results['mrr'])/(2*count), 5)

	for k in range(10):
		results['left_hits@{}'.format(k+1)]	= round(left_results ['hits@{}'.format(k+1)]/count, 5)
		results['right_hits@{}'.format(k+1)]	= round(right_results['hits@{}'.format(k+1)]/count, 5)
		results['hits@{}'.format(k+1)]		= round((left_results['hits@{}'.format(k+1)] + right_results['hits@{}'.format(k+1)])/(2*count), 5)
	return results

def get_combined_results(left_results, right_results):
	results = {}
	count   = float(left_results['count'])

	results['left_mr']	= round(left_results ['mr'] /count, 5)
	results['left_mrr']	= round(left_results ['mrr']/count, 5)
	results['right_mr']	= round(right_results['mr'] /count, 5)
	results['right_mrr']	= round(right_results['mrr']/count, 5)
	results['mr']		= round((left_results['mr']  + right_results['mr']) /(2*count), 5)
	results['mrr']		= round((left_results['mrr'] + right_results['mrr'])/(2*count), 5)

	for k in range(10):
		results['left_hits@{}'.format(k+1)]	= round(left_results ['hits@{}'.format(k+1)]/count, 5)
		results['right_hits@{}'.format(k+1)]	= round(right_results['hits@{}'.format(k+1)]/count, 5)
		results['hits@{}'.format(k+1)]		= round((left_results['hits@{}'.format(k+1)] + right_results['hits@{}'.format(k+1)])/(2*count), 5)
	return results

def get_param(shape):
	param = Parameter(torch.Tensor(*shape)); 	
	xavier_normal_(param.data)
	return param

def com_mult(a, b):
	r1, i1 = a[..., 0], a[..., 1]
	r2, i2 = b[..., 0], b[..., 1]
	return torch.stack([r1 * r2 - i1 * i2, r1 * i2 + i1 * r2], dim = -1)

def conj(a):
	a[..., 1] = -a[..., 1]
	return a

def cconv(a, b):
	# return torch.irfft(com_mult(torch.rfft(a, 1), torch.rfft(b, 1)), 1, signal_sizes=(a.shape[-1],))
	return irfft(com_mult(rfft(a, 1), rfft(b, 1)), 1, signal_sizes=(a.shape[-1],))

def ccorr(a, b):
	# return torch.irfft(com_mult(conj(torch.rfft(a, 1)), torch.rfft(b, 1)), 1, signal_sizes=(a.shape[-1],))
	return irfft(com_mult(conj(rfft(a, 1)), rfft(b, 1)), 1, signal_sizes=(a.shape[-1],))
