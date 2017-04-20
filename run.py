
print "----------------start setting environment"
import tensorflow as tf
print "tf"
import numpy as np
print "np"
import FCN1
print "FCN1"
import time
import sys
import os
print "sys"
sys.addpath('./')
from test_bd import dataFetch
from evaluate import testall
print "help"



def savemodel(modelname,saver,sess):
    print ("----------------start saving model")
    modeldir=('../network/'+modelname)  
    if not os.path.exists(modeldir):
        os.makedirs(modeldir)
    modeldir=(modeldir+'/'+modelname)  
    print 'save model to: %s'%(modeldir)
    saver.save(sess, modeldir)


objectNum=75
viewNum=3
selectorder=np.arange(objectNum*viewNum*512)


state="norandom"
rand=False
if sys.argv[1]=='random':
    state="random"
    rand=True
    selectorder=randomshuffle(selectorder)


size=16
epoch=15
quicktest=False
storelength=30
save=True
evaluate=True
restore=False
if sys.argv[2]=='quicktest':
    quicktest=True
    selectorder=np.arange(0,objectNum*viewNum*512,viewNum*512)
    selectorder=selectorder+2*512+256
    iterations=epoch 
    storelength=4
elif sys.argv[2]=='test1':
    epoch=1
    


iterationsOne=len(selectorder)/size
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
    print "traindata: %d state: %s, epoch,iterations per epoch: %d,%d, gap: %d "%(len(selectorder),state,epoch,iterationsOne,gap)
    t0 = time()
    sess.run(init)
    if quicktest:
        state='quick'+state
        imgs=np.load('../bigfile/testimgs.npy')
        segs=np.load('../bigfile/testsegs.npy')
    for epochind in range(epoch):
        modelname=('model_%s_%d_%d'%(state,epoch,epochind))
        modelfolddir=('../network/'+modelname)  
        if restore and os.path.exists(modelfolddir):
            print ('start loading model_%d_%s_%s'%(epoch,state,quicktest))            
            modeldir=('../network/%s/%s'%(modelname,modelname))
            saver.restore(sess,modeldir)
        else:
            for iterind in range(iterationsOne):
                pos=0
                if not quicktest:
                    pos,sample=next_batch(pos,size,selectorder)    
                    imgs=mydataFetch.getdata(sample,'train','img')
                    segs=mydataFetch.getdata(sample,'train','seg')
                    imgs=prepareX(imgs)
                    segs=prepareY(segs,number_of_classes)
                train_step.run(feed_dict={x: imgs, y_: segs, keep_prob: 0.5}) 
                if iterind%gap == 0 or iterind==iterationsOne-1:
                    cp=correct_prediction.eval(feed_dict={x: imgs, y_: segs,keep_prob: 1.0})
                    ce=cross_entropy.eval(feed_dict={x: imgs, y_: segs,keep_prob: 1.0})
                    ac=np.mean(cp)
                    ac2=np.mean(cp[1:])
                    print("epoch: %d,step: %d, training accuracy %.4f, only label: %.4f, loss %g, time %d"%(epochind,iterind, ac,ac2,ce,time()-t0))
                    t0 = time()
                    del cp,ce,ac,ac2
            if save:
                savemodel(modelname,saver,sess)
                epochind=epochind+1
                print "successfully save model"
            if rand:
                selectorder=randomshuffle(selectorder)
        if evaluate:
            resdir='../res/%s_%d_%d/'%(state,epoch,epochind)
            testall(sess,result,number_of_classes,x,y_,keep_prob,quicktest=quicktest,resdir=resdir,saveres=True)




