import tensorflow as tf
import numpy as np
import os
import shutil
import matplotlib.pyplot as plt
import glob
from models import ANN_model
from fedml import Fed_Training
import datetime

# gpus = tf.config.experimental.list_physical_devices(device_type='GPU')
# tf.config.experimental.set_virtual_device_configuration( gpus[0], [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=3500)])

# data 
index_collection=glob.glob('worker_nodes/*/index.npy')
central_weight_path=os.path.join('central_node','ANN_model.h5')
(_, _), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()

# build central folder & start_up model
model=ANN_model()
shutil.rmtree('central_node', ignore_errors=True)
os.makedirs('central_node')
model.save_weights(central_weight_path)


###################################################################################################
my_EPO = 5000
loc_EPO = 1
early_STOP = 500
usual_node_NUMBER = 32
delayed_node_NUMBER = 8
shared_node_NUMBER = 0
delayed_SPEED = 3
SCENARIO='2c.40w.4000.dly{}.speed{}'.format(delayed_node_NUMBER,delayed_SPEED)
###################################################################################################

epo = my_EPO
loc_epoch = loc_EPO
patience = early_STOP
non_delayed_index = index_collection[:usual_node_NUMBER]
print('non_delayed_index')
print(len(non_delayed_index))

delayed_index=index_collection[usual_node_NUMBER:usual_node_NUMBER+delayed_node_NUMBER]
delayed_speed=delayed_SPEED
print('delayed_index')
print(len(delayed_index))

shared_index=index_collection[usual_node_NUMBER+delayed_node_NUMBER:usual_node_NUMBER+delayed_node_NUMBER+shared_node_NUMBER]
print('shared_index')
print(len(shared_index))


# initialize
train = Fed_Training(model,non_delayed_index,central_weight_path,x_test, y_test,batch_size=50,augument=False)
train.load_test_set()

# set delayed index
if delayed_index!=[]:
    train.set_delayed_update(delayed_index,delayed_speed)

# set shared index
if shared_index!=[]:
    train.set_shared_index(shared_index)

# do training
epo_h,loss_h,acc_h=train.fit(epo,patience,local_epoch=loc_epoch)

# Save result
arr = np.array([epo_h,loss_h,acc_h])
scenario=SCENARIO+'.'
uniq=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

filename=scenario+'loc{}.earlystop{}.'.format(loc_epoch,patience)+uniq+'.npy' 
filepath=os.path.join('result',filename)
np.save(filepath,arr)

# Save shared index & its weight
if shared_index!=[]:
    model.load_weights(central_weight_path)
    mod_n=scenario+'loc{}.earlystop{}.'.format(loc_epoch,patience)+uniq+'.h5'
    mod_dir=os.path.join('result','model_result',mod_n)
    model.save_weights(mod_dir)

    filename='index.'+scenario+'loc{}.earlystop{}.'.format(loc_epoch,patience)+uniq+'.npy' 
    np_dir=os.path.join('result',filename)
    np.save(np_dir, shared_index)
