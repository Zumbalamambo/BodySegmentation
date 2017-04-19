import tensorflow as tf
import FCN1
from PIL import Image
import numpy as np
import tensorflow as tf
import time
import sys
import os
from scipy.misc import imsave
from sklearn.model_selection import train_test_split
from test_bd import *
from evaluate import *

def savemodel(modelname,saver,sess):
    print ("----------------start saving model")
    modeldir=('../network/'+modelname)  
    if not os.path.exists(modeldir):
        os.makedirs(modeldir)
    modeldir=(modeldir+'/'+modelname)  
    print 'save model to: %s'%(modeldir)
    saver.save(sess, modeldir)





# python run [quicktest/noquicktest] [evaluate/noevaluate] [random/norandom] [startecho] [endecho] 
print "----------------start setting environment"
objectNum=75
viewNum=3
selectorder=np.arange(objectNum*viewNum*512)


randomstate="norandom"
if sys.argv[1]=='random':
    randomstate="random"
    selectorder=randomshuffle(selectorder)


size=16
epoch=15
quicktest=False
storelength=30
if sys.argv[2]=='quicktest':
    quicktest=True
    selectorder=np.arange(0,objectNum*viewNum*512,viewNum*512)
    selectorder=selectorder+2*512+256
    iterations=epoch 
    storelength=4
elif sys.argv[2]=='test1':
    epoch=1
    


iterationsOne=len(selectorder)/size
iterations=epoch*iterationsOne
gap=iterationsOne//10
mydataFetch=dataFetch(storelength)
if gap<1:
    gap=1
    
print "----------------start building network"
number_of_classes=19
speed=1e-5
#Network structure--------------------------                                 
#sess = tf.InteractiveSession()
x = tf.placeholder(tf.float32, shape=[None,512,512,3])
y_ = tf.placeholder(tf.float32, shape=[None,512,512,number_of_classes])


keep_prob = tf.placeholder(tf.float32)
y_conv=FCN1.FCN(x,keep_prob,number_of_classes=number_of_classes)
cross_entropy = tf.reduce_mean(
    tf.nn.softmax_cross_entropy_with_logits(labels=y_, logits=y_conv))

train_step = tf.train.AdamOptimizer(speed).minimize(cross_entropy)
correct_prediction = tf.equal(tf.argmax(y_conv,3), tf.argmax(y_,3))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
result =tf.argmax(y_conv,3)
init=tf.global_variables_initializer()
saver = tf.train.Saver()

with tf.Session() as sess:
    #training--------------------------
    print "----------------start training"
    pos=0
    t0 = time()
    epochind=0
    sess.run(init)
    for i in range(iterations):
        if sys.argv[3]=='quicktest':
            imgs=np.load('../bigfile/testimgs.npy')
            segs=np.load('../bigfile/testsegs.npy')
        else:
            pos,sample=next_batch(pos,size,selectorder)    
            imgs=mydataFetch.getdata(sample,'train','img')
            segs=mydataFetch.getdata(sample,'train','seg')
            imgs=prepareX(imgs)
            segs=prepareY(segs,number_of_classes)
        if i==0:
            print "traindata: %d randomstate: %s, echo,iterations: %d,%d, gap: %d "%(len(selectorder),randomstate,epoch,iterations,gap)
        if i%gap == 0 or i==iterations-1:
            cp=correct_prediction.eval(feed_dict={x: imgs, y_: segs,keep_prob: 1.0})
            ce=cross_entropy.eval(feed_dict={x: imgs, y_: segs,keep_prob: 1.0})
            ac=np.mean(cp)
            ac2=np.mean(cp[1:])
            print("step %d, training accuracy %.4f, only label: %.4f, loss %g, time %d"%(i, ac,ac2,ce,time()-t0))
            t0 = time()
            del cp,ce,ac,ac2
        train_step.run(feed_dict={x: imgs, y_: segs, keep_prob: 0.5})
        if i % (len(selectorder)/size)==0:
            if randomstate=="random":
                selectorder=randomshuffle(selectorder)
            modelname=('model_%d_%s_%s_%d'%(epoch,randomstate,sys.argv[3],epochind))
            savemodel(modelname,saver,sess)
            epochind=epochind+1
            print "successfully save model"
        

#testing---------------------------
    

    resdir='../res/%s_%s_%s_final/'%(sys.argv[1],sys.argv[2],sys.argv[3])
    testall(sess,result,x,y_,keep_prob,quicktest=quicktest,resdir=resdir,number_of_classes=number_of_classes,saveres=True)




