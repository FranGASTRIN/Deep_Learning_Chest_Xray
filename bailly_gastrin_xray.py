# -*- coding: utf-8 -*-
"""Bailly_Gastrin_Xray.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zSwGA6KL5r_eyjUVuoY93jHiqKQ3fvoy

# Modules
"""

import os
import numpy as np
import cv2
import glob
import pandas as pd
import random as rn

import seaborn
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from keras import layers
from keras import preprocessing
from keras.preprocessing.image import ImageDataGenerator
from keras.applications.vgg16 import VGG16
from keras.applications.resnet_v2 import ResNet50V2
from keras.applications.inception_v3 import InceptionV3
from keras.applications.densenet import DenseNet201
from sklearn.metrics import confusion_matrix
from statistics import stdev

print(tf.__version__)

"""# Data processing

Remplacez les chemins par les votres
"""

# Chemin du dossier chest_xray
global_path = "./drive/MyDrive/chest_xray/"
os.listdir(global_path)

# Chemin des dossiers normal/pneumonie pour le jeu test et train
train_normal_path = global_path + 'train/NORMAL/'
train_pneu_path = global_path + 'train/PNEUMONIA/'

test_normal_path = global_path + 'test/NORMAL/'
test_pneu_path = global_path + 'test/PNEUMONIA/'

train_normal_img = glob.glob(train_normal_path + '*jpeg')
train_pneu_img = glob.glob(train_pneu_path + '*jpeg')

test_normal_img = glob.glob(test_normal_path + '*jpeg')
test_pneu_img = glob.glob(test_pneu_path + '*jpeg')

# Création de liste contenant les images et la classe de chaque image
train_list = []
test_list = []

for x in train_normal_cases:
    train_list.append([x, 0])
    
for x in train_pneu_cases:
    train_list.append([x, 1])
    
for x in test_normal_cases:
    test_list.append([x, 0])
    
for x in test_pneu_cases:
    test_list.append([x, 1])

rn.shuffle(train_list)
rn.shuffle(test_list)

# Création de dataframe
train_df = pd.DataFrame(train_list, columns=['image', 'label'])
test_df = pd.DataFrame(test_list, columns=['image', 'label'])

# Countplot des jeux de données
plt.figure(figsize=(20,5))

plt.subplot(1,3,1)
seaborn.countplot(train_df['label'])
plt.title('Train data')

plt.subplot(1,3,2)
seaborn.countplot(test_df['label'])
plt.title('Test data')

plt.show()

def process_data(img_path):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (150, 150))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = img/255.0
    img = np.reshape(img, (150,150,1))
    
    return img

def build_dataset(df):
    data = []
    labels = []

    for img_path, label in df.values:
        data.append(process_data(img_path))
        labels.append(label)
        
    return np.array(data), np.array(labels)

X_train, y_train = build_dataset(train_df)
X_test, y_test = build_dataset(test_df)

print('Train data shape: {}, Labels shape: {}'.format(X_train.shape, y_train.shape))
print('Test data shape: {}, Labels shape: {}'.format(X_test.shape, y_test.shape))

# Commented out IPython magic to ensure Python compatibility.
# %cd drive
# %cd MyDrive/
# %cd data_npz/
!ls

# Commented out IPython magic to ensure Python compatibility.
# %cp xray_test.npz /content/
# %cp xray_train.npz /content/

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/

# Sauvegarde des jeux de données

np.savez("xray_train.npz",X_train = X_train, y_train = y_train)
np.savez("xray_test.npz", X_test = X_test, y_test = y_test)

# A décommenter quand on utilise les fichiers npz

'''train_file = "xray_train.npz"
data_train = np.load(train_file)
X_train = data_train["X_train"]
y_train = data_train["y_train"]'''
X_train = X_train.astype("float32")

'''test_file = "xray_test.npz"
data_test = np.load(test_file)
X_test = data_test["X_test"]
y_test = data_test["y_test"]'''
X_test = X_test.astype("float32")

"""# CNN

Pour toute cette partie on restera sur 10 époques, car des tests précédents réaliser sur un nombre plus important d'époques sans et avec Early Stopping nous à montrer que l'apprentissage dépasse rarement les 10 époques et de façon plus large ne dépasse pas les 12-14 époques.

## Initialisation des poids

De par le léger déséquilibre entre les classes dans les jeux de données nous avons décidé d'initialiser les poids.

Les valeurs des poids initiales ont été choisies par des tests préalablement réalisés sur un réseau CNN très simple.

weight_0 = $\frac {1}{n_{normal}} \times \frac {n_{total}}{2}$

weight_1 = $\frac {1}{n_{pneumonie}} \times \frac {n_{total}}{2}$
"""

w0 = (1/(len(y_train) - np.count_nonzero(y_train))) * (len(y_train)/2)
w1 = (1/(np.count_nonzero(y_train))) * (len(y_train)/2)

cl_weights = {0: w0,
              1: w1}

"""## test des paramètre de la data Augmentation

Le réseau utilisé pour ces tests est un réseau obtenu après avoir effectué différents aux préalables en s'inspirant de réseau provenant de notebook sur kaggle.

Nous en avons conclu qu'un modèle simple avec relativement peu de paramètres serait amplement suffisant.
"""

def block_conv(input, filters):
  x = layers.Conv2D(filters, 3, activation='relu')(input)
  x = layers.BatchNormalization()(x)
  x = layers.MaxPooling2D(2)(x)
  return(x)

inputs = layers.Input(shape=(150, 150, 1 ))

bc1 = block_conv(inputs, 16)

bc2 = block_conv(bc1, 32)

bc3 = block_conv(bc2, 64)

bc4 = block_conv(bc3, 128)

flat_1 = layers.Flatten()(bc4)
dense_1 = layers.Dense(32)(flat_1)
drop_1 = layers.Dropout(0.2)(dense_1)
outputs = layers.Dense(1, activation='sigmoid')(drop_1)

CNN_model = keras.Model(inputs, outputs)

print(CNN_model.summary())

"""### Sans data augmentation"""

datagen_sd = ImageDataGenerator(
    validation_split = 0.1
)

"""Affichage de 3 images non modifiées"""

# iterator
sample = X_train[1214:1217]

aug_iter = datagen_sd.flow(sample)

# generate samples and plot
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(150,150))

# generate batch of images
for i in range(3):

	# convert to unsigned integers
	image = next(aug_iter)[0,:,:,0]
 
	# plot image
	ax[i].imshow(image, cmap="gray")
	ax[i].axis('off')

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_CNN = CNN_model.fit(
    datagen_sd.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_sd.flow(X_train, y_train, subset="validation")
)

test_sd = CNN_model.evaluate(X_test, y_test)
print(test_sd)

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_CNN.epoch, y=history_CNN.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_CNN.epoch, y=history_CNN.history['val_loss'], color='orange', label='test Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_CNN.epoch, y=history_CNN.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_CNN.epoch, y=history_CNN.history['val_accuracy'], color='green', label='test Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""### Rotation"""

datagen_r = ImageDataGenerator(
    validation_split = 0.1,
    rotation_range = 10
)

# iterator
sample = X_train[1214:1217]

aug_iter = datagen_r.flow(sample)

# generate samples and plot
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(150,150))

# generate batch of images
for i in range(3):

	# convert to unsigned integers
	image = next(aug_iter)[0,:,:,0]
 
	# plot image
	ax[i].imshow(image, cmap="gray")
	ax[i].axis('off')

"""ne pas oublier de relancer la cellule de création du modèle"""

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_r = CNN_model.fit(
    datagen_r.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_r.flow(X_train, y_train, subset="validation")
)

test_r = CNN_model.evaluate(X_test, y_test)
print(test_r)

"""La rotation améliore les performance du modèle"""

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_r.epoch, y=history_r.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_r.epoch, y=history_r.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_r.epoch, y=history_r.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_r.epoch, y=history_r.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""### Shift"""

datagen_sh = ImageDataGenerator(
    validation_split = 0.1,
    width_shift_range=0.1,
    height_shift_range=0.1
)

# iterator
sample = X_train[1214:1217]

aug_iter = datagen_sh.flow(sample)

# generate samples and plot
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(150,150))

# generate batch of images
for i in range(3):

	# convert to unsigned integers
	image = next(aug_iter)[0,:,:,0]
 
	# plot image
	ax[i].imshow(image, cmap="gray")
	ax[i].axis('off')

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_sh = CNN_model.fit(
    datagen_r.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_sh.flow(X_train, y_train, subset="validation")
)

test_sh = CNN_model.evaluate(X_test, y_test)
print(test_sh)

"""le shift n'apporte rien la valeur est quasi identique avec sans data augmatation

### Zoom
"""

datagen_z = ImageDataGenerator(
    zoom_range = 0.1,
    validation_split = 0.1 
)

# iterator
sample = X_train[1214:1217]

aug_iter = datagen_z.flow(sample)

# generate samples and plot
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(150,150))

# generate batch of images
for i in range(3):

	# convert to unsigned integers
	image = next(aug_iter)[0,:,:,0]
 
	# plot image
	ax[i].imshow(image, cmap="gray")
	ax[i].axis('off')

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_z = CNN_model.fit(
    datagen_z.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_z.flow(X_train, y_train, subset="validation")
)

test_z = CNN_model.evaluate(X_test, y_test)
print(test_z)

"""L'ajout d'un zoom aléatoirement améliore nettement les perfomances du modèle."""

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_z.epoch, y=history_z.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_z.epoch, y=history_z.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_z.epoch, y=history_z.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_z.epoch, y=history_z.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""### Brightness_range"""

datagen_br = ImageDataGenerator(
    brightness_range = [0.5,1.5],
    validation_split = 0.1 
)

# iterator
sample = X_train[1214:1217]

aug_iter = datagen_br.flow(sample)

# generate samples and plot
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(150,150))

# generate batch of images
for i in range(3):

	# convert to unsigned integers
	image = next(aug_iter)[0,:,:,0]
 
	# plot image
	ax[i].imshow(image, cmap="gray")
	ax[i].axis('off')

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_br = CNN_model.fit(
    datagen_br.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_br.flow(X_train, y_train, subset="validation")
)

test_br = CNN_model.evaluate(X_test, y_test)
print(test_br)

"""### Shear range"""

datagen_sr = ImageDataGenerator(
    shear_range = 10,
    validation_split = 0.1 
)

# iterator
sample = X_train[1214:1217]

aug_iter = datagen_sr.flow(sample)

# generate samples and plot
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(150,150))

# generate batch of images
for i in range(3):

	# convert to unsigned integers
	image = next(aug_iter)[0,:,:,0]
 
	# plot image
	ax[i].imshow(image, cmap="gray")
	ax[i].axis('off')

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_sr = CNN_model.fit(
    datagen_sr.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_sr.flow(X_train, y_train, subset="validation")
)

test_sr = CNN_model.evaluate(X_test, y_test)
print(test_sr)

"""Le shear range augment également les performances du modèle"""

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_sr.epoch, y=history_sr.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_sr.epoch, y=history_sr.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_sr.epoch, y=history_sr.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_sr.epoch, y=history_sr.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""### Rotation + Zoom + Shear range"""

datagen_true = ImageDataGenerator(
    rotation_range=10,
    zoom_range = 0.1,
    shear_range = 10,
    validation_split = 0.1 
)

# iterator
sample = X_train[1214:1217]

aug_iter = datagen_true.flow(sample)

# generate samples and plot
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(150,150))

# generate batch of images
for i in range(3):

	# convert to unsigned integers
	image = next(aug_iter)[0,:,:,0]
 
	# plot image
	ax[i].imshow(image, cmap="gray")
	ax[i].axis('off')

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_CNN_true = CNN_model.fit(
    datagen_true.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_true.flow(X_train, y_train, subset="validation")
)

test_CNN_true = CNN_model.evaluate(X_test, y_test)
print(test_CNN_true)

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_CNN_true.epoch, y=history_CNN_true.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_CNN_true.epoch, y=history_CNN_true.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_CNN_true.epoch, y=history_CNN_true.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_CNN_true.epoch, y=history_CNN_true.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""Pour la suite on gardera datagen_true comme ImageDataGenerator

## Comparaison d'initialisation différente des poids

### Méthode 1

cf Test des paramètres de la data augmentation : rotation + zoom + shear range

### Méthode 2

Dans le jeu d'entraînement il y a 74% d'image de la classe 1 (pneumonie) et 26% pour la classe 0 (normal) on utilisera donc ces valeurs pour initier les poids de cette façon :
"""

cl_w_2 = {0 : 0.74,
          1 : 0.26}

"""on réutilise CNN_model"""

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_w2 = CNN_model.fit(
    datagen_true.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_w_2,
    validation_data= datagen_true.flow(X_train, y_train, subset="validation")
)

test_w2 = CNN_model.evaluate(X_test, y_test)
print(test_w2)

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_w2.epoch, y=history_w2.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_w2.epoch, y=history_w2.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_w2.epoch, y=history_w2.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_w2.epoch, y=history_w2.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""L'accuracy sur le test est similaire avec le résultat de la méthode 1.

La courbe des val loss est un tout petit peu moins stable et les courbes d'accuracy montrent de plus grandes variations que pour la méthode 1.

On décide donc de garder cette dernière pour l'initialisation des poids.

### Méthode 3

On décide de réessayer avec une initialisation aléatoire des poids.
"""

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_w3 = CNN_model.fit(
    datagen_true.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10,
    validation_data= datagen_true.flow(X_train, y_train, subset="validation")
)

test_w3 = CNN_model.evaluate(X_test, y_test)
print(test_w3)

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_w3.epoch, y=history_w3.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_w3.epoch, y=history_w3.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_w3.epoch, y=history_w3.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_w3.epoch, y=history_w3.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""## Intervalle de Confiance sur l'accuracy test"""

res = []

for i in range(0, 10, 1):
##### Data generator for data augmentation
  augmented_data = ImageDataGenerator(
                  rotation_range = 10,
                  zoom_range = 0.1,
                  shear_range = 10,
                  validation_split = 0.1
)
  
##### Model compilation
  inputs = layers.Input(shape=(150, 150, 1 ))

  bc1 = block_conv(inputs, 16)

  bc2 = block_conv(bc1, 32)

  bc3 = block_conv(bc2, 64)

  bc4 = block_conv(bc3, 128)

  flat_1 = layers.Flatten()(bc4)
  dense_1 = layers.Dense(32)(flat_1)
  drop_1 = layers.Dropout(0.2)(dense_1)
  outputs = layers.Dense(1, activation='sigmoid')(drop_1)

  CNN_model = keras.Model(inputs, outputs)

  CNN_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

##### Fitting
  history_bas = CNN_model.fit(augmented_data.flow(x_train, y_train, subset="training"), batch_size = 32, epochs = 10, 
                            validation_data = augmented_data.flow(x_train, y_train, subset="validation"), class_weight = class_weight)
  
##### Evaluation
  eval = CNN_model.evaluate(x_test, y_test)
  res.append(eval[1])

1.65*(stdev(res)/((len(res)**(1/2))))*100

"""Lors de l'éxecution on a obtenu cette intervalle :
$90.4 \pm 1.9$

## Variation du Learning Rate

jusqu'à présent on laissait le learning rate de base soit 0.001.

Nous allons faire varier cette valeur et observer les résultats.

On utilisera le modèle : CNN_model et l'ImageDataGenerator : datagen_true

### Learning Rate : 0.001

cf Test des paramètres de la data augmentation : rotation + zoom + shear range

### Learning Rate : 0.1
"""

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.1),
    metrics=["accuracy"]
)

history_LR01 = CNN_model.fit(
    datagen_true.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_true.flow(X_train, y_train, subset="validation")
)

test_LR01 = CNN_model.evaluate(X_test, y_test)
print(test_LR01)

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_LR01.epoch, y=history_LR01.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_LR01.epoch, y=history_LR01.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_LR01.epoch, y=history_LR01.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_LR01.epoch, y=history_LR01.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""L'accuracy sur le test est de 0.80, soit 10% de moins qu'avec le Learning Rate de base.

### Learning Rate : 0.01
"""

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.01),
    metrics=["accuracy"]
)

history_LR001 = CNN_model.fit(
    datagen_true.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_true.flow(X_train, y_train, subset="validation")
)

test_LR001 = CNN_model.evaluate(X_test, y_test)
print(test_LR001)

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_LR001.epoch, y=history_LR001.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_LR001.epoch, y=history_LR001.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_LR001.epoch, y=history_LR001.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_LR001.epoch, y=history_LR001.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""Le résultat de l'accuracy sur le jeu de test est plus faible que pour un LR de 0.1 et 0.001. On voit que les courbes ne sont pas stable du tout la loss et l'accuracy varie beacoup, tandis qu'idéalement elle devrait respectivement décroître et croître avant d'atteindre un plateau proche de la valeur pour le jeu train.

### Learning Rate : 0.0001
"""

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.01),
    metrics=["accuracy"]
)

history_LR00001 = CNN_model.fit(
    datagen_true.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_true.flow(X_train, y_train, subset="validation")
)

test_LR00001 = CNN_model.evaluate(X_test, y_test)
print(test_LR00001)

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_LR00001.epoch, y=history_LR00001.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_LR00001.epoch, y=history_LR00001.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_LR00001.epoch, y=history_LR00001.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_LR00001.epoch, y=history_LR00001.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""Encore une fois la valeur de l'accuracy sur le jeu de test est inférieure à ce qu'on obtiens avec le learning rate de 0.001.

Les courbes de val loss et val accuracy montre également plus de variation.

### Learning Rate : 0.00001
"""

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.01),
    metrics=["accuracy"]
)

history_LR000001 = CNN_model.fit(
    datagen_true.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_true.flow(X_train, y_train, subset="validation")
)

test_LR000001 = CNN_model.evaluate(X_test, y_test)
print(test_LR000001)

"""Ce pas semble trop petit, la valeur d'accuracy obtenue sur le jeu test est de 0.625, ce qui correspond également à la proportion de pneumonie dans le jeu test, ce qui signifie qu'il classe toutes les images en pneumonie, comme le montre la matrice de confusion suivante :"""

prediction = CNN_model.predict(X_test)
y_pred = np.round(prediction,0)
print(confusion_matrix(y_test, y_pred))

"""Pour la suite on va donc garder le même Learing Rate que d'habitude, celui de base valant : 0.001

## Modification de l'architecture

#### Deux Conv2D avant la Batch normalization
"""

def doubleblock_conv(input, filters):
  x = layers.Conv2D(filters, 3, activation='relu')(input)
  x = layers.Conv2D(filters, 3, activation='relu')(x)
  x = layers.BatchNormalization()(x)
  x = layers.MaxPooling2D(2)(x)
  return(x)

inputs = layers.Input(shape=(150, 150, 1 ))

bc1 = doubleblock_conv(inputs, 16)

bc2 = doubleblock_conv(bc1, 32)

bc3 = doubleblock_conv(bc2, 64)

bc4 = doubleblock_conv(bc3, 128)

flat_1 = layers.Flatten()(bc4)
dense_1 = layers.Dense(32)(flat_1)
drop_1 = layers.Dropout(0.2)(dense_1)
outputs = layers.Dense(1, activation='sigmoid')(drop_1)

model_DC = keras.Model(inputs, outputs)

print(model_DC.summary())

"""On voit que le nombre de paramètre a légèrement augmenter, la différence ce fait sur la profondeur du réseau."""

model_DC.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_DC = model_DC.fit(
    datagen_true.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_true.flow(X_train, y_train, subset="validation")
)

test_DC = model_DC.evaluate(X_test, y_test)
print(test_DC)

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_DC.epoch, y=history_DC.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_DC.epoch, y=history_DC.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_DC.epoch, y=history_DC.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_DC.epoch, y=history_DC.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""La valeur d'accuracy sur le jeu de test est relativement bonne 0.85. La val loss a bien diminue avant de remonter un petit peu.

### Augmentation du Kernel size
"""

def block_kernel(input, filters, kernel):
  x = layers.Conv2D(filters, kernel, activation='relu')(input)
  x = layers.BatchNormalization()(x)
  x = layers.MaxPooling2D(2)(x)
  return(x)

inputs = layers.Input(shape=(150, 150, 1 ))

bc1 = block_kernel(inputs, 16, 7)

bc2 = block_kernel(bc1, 32, 7)

bc3 = block_kernel(bc2, 64, 7)

bc4 = block_kernel(bc3, 128, 7)

flat_1 = layers.Flatten()(bc4)
dense_1 = layers.Dense(32)(flat_1)
drop_1 = layers.Dropout(0.2)(dense_1)
outputs = layers.Dense(1, activation='sigmoid')(drop_1)

model_K1 = keras.Model(inputs, outputs)

print(model_K1.summary())

model_K1.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_K1 = model_K1.fit(
    datagen_true.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_true.flow(X_train, y_train, subset="validation")
)

test_K1 = model_K1.evaluate(X_test, y_test)
print(test_K1)

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_K1.epoch, y=history_K1.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_K1.epoch, y=history_K1.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_K1.epoch, y=history_K1.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_K1.epoch, y=history_K1.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""### Deux Conv avant la Batch normalization + variation du kernel size

Ce modèle correspond à un modèle vu sur kaggle, sur lequel nous avions effectuer des test. Il fait partie des 2 modèles que nous avons prit sur kaggle.
"""

inputs = layers.Input(shape=(150, 150, 1 ))

bc1 = doubleblock_kernel(inputs, 16, 7)

bc2 = doubleblock_kernel(bc1, 32, 5)

bc3 = doubleblock_kernel(bc2, 64, 3)

flat_1 = layers.Flatten()(bc3)
dense_1 = layers.Dense(32)(flat_1)
drop_1 = layers.Dropout(0.2)(dense_1)
outputs = layers.Dense(1, activation='sigmoid')(drop_1)

model_DK = keras.Model(inputs, outputs)

print(model_DK.summary())

"""On constate que ce modèle possède 3 fois plus de paramètres que CNN_model, et plus de 2 fois plus que model_DC."""

model_DK.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_DK = model_DK.fit(
    datagen_true.flow(X_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight=cl_weights,
    validation_data= datagen_true.flow(X_train, y_train, subset="validation")
)

test_DK = model_DK.evaluate(X_test, y_test)
print(test_DK)

plt.figure(figsize=(20,5))

# plot loss & val loss
plt.subplot(1,2,1)
seaborn.lineplot(x=history_DK.epoch, y=history_DK.history['loss'], color='red', label='Loss')
seaborn.lineplot(x=history_DK.epoch, y=history_DK.history['val_loss'], color='orange', label='val Loss')
plt.title('Loss on train vs validation')
plt.legend(loc='best')

# plot accuracy and val accuracy
plt.subplot(1,2,2)
seaborn.lineplot(x=history_DK.epoch, y=history_DK.history['accuracy'], color='blue', label='Accuracy')
seaborn.lineplot(x=history_DK.epoch, y=history_DK.history['val_accuracy'], color='green', label='val Accuracy')
plt.title('Accuracy on train vs validation')
plt.legend(loc='best')

plt.show()

"""# Transfert learning

## VGG16
"""

x_Gtrain = X_train[:,:,:,0]
x_Gtest = X_test[:,:,:,0]

rgb_x_train = np.repeat(x_Gtrain[..., np.newaxis], 3, -1)
rgb_x_test = np.repeat(x_Gtest[..., np.newaxis], 3, -1)

print(rgb_x_train.shape)
print(rgb_x_test.shape)

inputs = layers.Input(shape=(150, 150, 3))
vgg_model = VGG16(include_top= False,
                     weights = "imagenet",
)
vgg_model.trainable = False

base = vgg_model(inputs, training = False)
#avg_1 = layers.GlobalAveragePooling2D()(base)
#drop_1 = layers.Dropout(0.5)(avg_1)
#dense_1 = layers.Dense(32)(drop_1)
flat1 = layers.Flatten()(base)
outputs = layers.Dense(1, activation='sigmoid')(flat1)

TL_VGG = keras.Model(inputs, outputs)

TL_VGG.summary()

TL_VGG.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_VGG = TL_VGG.fit(
    datagen_true.flow(rgb_x_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight = cl_weights,
    validation_data= datagen_true.flow(rgb_x_train, y_train, subset="validation")
)

test_VGG = TL_VGG.evaluate(rgb_x_test, y_test)
print(test_VGG)

"""## ResNet50V2"""

inputs = layers.Input(shape=(150, 150, 3))
RNV2_model = ResNet50V2(include_top= False,
                     weights = "imagenet",
)
RNV2_model.trainable = False

base = RNV2_model(inputs, training = False)
#avg_1 = layers.GlobalAveragePooling2D()(base)
#drop_1 = layers.Dropout(0.5)(avg_1)
#dense_1 = layers.Dense(32)(drop_1)
flat1 = layers.Flatten()(base)
outputs = layers.Dense(1, activation='sigmoid')(flat1)

TL_RNV2 = keras.Model(inputs, outputs)

TL_RNV2.summary()

TL_RNV2.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_RNV2 = TL_RNV2.fit(
    datagen_true.flow(rgb_x_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight = cl_weights,
    validation_data= datagen_true.flow(rgb_x_train, y_train, subset="validation")
)

test_RNV2 = TL_RNV2.evaluate(rgb_x_test, y_test)
print(test_RNV2)

"""## InceptionV3"""

inputs = layers.Input(shape=(150, 150, 3))
InV3_model = InceptionV3(include_top= False,
                     weights = "imagenet",
)
InV3_model.trainable = False

base = InV3_model(inputs, training = False)
#avg_1 = layers.GlobalAveragePooling2D()(base)
#drop_1 = layers.Dropout(0.5)(avg_1)
#dense_1 = layers.Dense(32)(drop_1)
flat1 = layers.Flatten()(base)
outputs = layers.Dense(1, activation='sigmoid')(flat1)

TL_InV3 = keras.Model(inputs, outputs)

TL_InV3.summary()

TL_InV3.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_InV3 = TL_InV3.fit(
    datagen_true.flow(rgb_x_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight = cl_weights,
    validation_data= datagen_true.flow(rgb_x_train, y_train, subset="validation")
)

test_InV3 = TL_InV3.evaluate(rgb_x_test, y_test)
print(test_InV3)

"""## DenseNet201"""

inputs = layers.Input(shape=(150, 150, 3))
DN201_model = DenseNet201(include_top= False,
                     weights = "imagenet",
)
DN201_model.trainable = False

base = DN201_model(inputs, training = False)
#avg_1 = layers.GlobalAveragePooling2D()(base)
#drop_1 = layers.Dropout(0.5)(avg_1)
#dense_1 = layers.Dense(32)(drop_1)
flat1 = layers.Flatten()(base)
outputs = layers.Dense(1, activation='sigmoid')(flat1)

TL_DN201 = keras.Model(inputs, outputs)

TL_DN201.summary()

TL_DN201.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

history_DN201 = TL_DN201.fit(
    datagen_true.flow(rgb_x_train, y_train, batch_size=32, subset="training"),
    epochs=10, class_weight = cl_weights,
    validation_data= datagen_true.flow(rgb_x_train, y_train, subset="validation")
)

test_DN201 = TL_DN201.evaluate(rgb_x_test, y_test)
print(test_DN201)

"""# Comparaison

Model_TF = CNN_model
"""

df_Recap = pd.DataFrame(columns=["Accuracy test","Sensiti.(%)","Specifi.(%)","Number of Parameters"],
                     index=["Model_TF", "Model_DC","Model_K1","Model_DK","TL_VGG",
                            "TL_ResNet50V2","TL_InceptionV3","TL_DenseNet201"],
                     data=[[0.924, (363/390)*100, (214/234)*100, "298 881"],
                           [0.846, (387/390)*100, (141/234)*100, "396 657"],
                           [0.868, (385/390)*100, (157/234)*100, "565 761"],
                           [0.873, (385/390)*100, (160/234)*100, "906 785"],
                           [0.877, (341/390)*100, (206/234)*100, "14 722 881"],
                           [0.888, (364/390)*100, (190/234)*100, "23 616 001"],
                           [0.859, (372/390)*100, (164/234)*100, "21 821 217"],
                           [0.881, (366/390)*100, (184/234)*100, "18 352 705"],])

print(df_Recap)

"""# Observation résultat

Pour cette partie on réutilise les meilleur poids obtenu avec CNN_model
"""

CNN_model.load_weights("./cnn_xray_pneumo.h5")

CNN_model.compile(
    loss="binary_crossentropy",
    optimizer= keras.optimizers.Adam(learning_rate= 0.001),
    metrics=["accuracy"]
)

CNN_model.evaluate(X_test, y_test)

prediction = CNN_model.predict(X_test)
y_pred = np.round(prediction,0)
print(confusion_matrix(y_test, y_pred))

cm_y_pred = confusion_matrix(y_test, y_pred)

df_pred = pd.DataFrame(cm_y_pred , index = ['0','1'] , columns = ['0','1'])

df_pred

y_pred[:15]

liste_pred = []
for elem in y_pred:
  liste_pred.append(elem[0])

arr_pred = np.asarray(liste_pred)

arr_y = np.column_stack((y_test, arr_pred))

correct = []
incorrect = []
for i in range(len(y_test)):
  if arr_y[i][0] == arr_y[i][1]:
    correct.append(i)
  else:
    incorrect.append(i)



i = 0
for c in correct[7:13]:
    plt.subplot(3,2,i+1)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(X_test[c].reshape(150,150), cmap="gray", interpolation='none')
    plt.title("Predicted Class {} | True Class {}".format(int(y_pred[c]), y_test[c]))
    plt.tight_layout()
    i += 1

i = 0
for c in incorrect[7:13]:
    plt.subplot(3,2,i+1)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(X_test[c].reshape(150,150), cmap="gray", interpolation='none')
    plt.title("Predicted Class {} | True Class {}".format(int(y_pred[c]), y_test[c]))
    plt.tight_layout()
    i += 1