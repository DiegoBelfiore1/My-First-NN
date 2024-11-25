#Here I'm trying to implement my first Neural Network using Pytorch
#First it is necessary to import Torch and TorchVision

import torch
import torchvision

#now the first step: importing the dataset and building the variables
#I'm about to use the libraries from torchvision
#Here we work with a non linear approach, then we need to build a function called
#Dataset with two arguments, batch and test_batch fixed to 256

def Dataset (batch, test_batch = 256):

  #we want all the images to be transformed into tensors, then we use the
  #ToTensor function

  transform = torchvision.transforms.ToTensor()

  training_and_validation_dataset = torchvision.datasets.MNIST(
    root = ".data/",
    train = True,
    download = True,
    transform = transform
  )

  test_dataset = torchvision.datasets.MNIST(
    root = ".data/",
    train = False, #extremely useful to download another version of the MNIST to be sure about having new data
    download = True,
    transform = transform
  )

  #now it is necessary to build up our real iterable dataset variables
  #first we divide the data in two splits

  total_data_lenght = len(training_and_validation_dataset)
  training_split = int(total_data_lenght * 0.8)
  test_split = total_data_lenght - training_split #then it is 0.2

  training, validation = torch.utils.data.random_split(training_and_validation_dataset,[training_split, test_split])

  #It is the moment to load the data in a correctly sampled way

  training_iterable = torch.utils.data.DataLoader(
      dataset = training,
      batch_size = batch,
      shuffle = True,
      )

  validation_iterable = torch.utils.data.DataLoader(
      dataset = validation,
      batch_size = test_batch,
      shuffle = False,
      )

  test_iterable = torch.utils.data.DataLoader(
      dataset = validation,
      batch_size = test_batch,
      shuffle = False,
      )
  return training_iterable, validation_iterable, test_iterable

#let's see the shape of our data

training_iterable, validation_iterable, test_iterable = Dataset(32) #batch32

for t in training_iterable:
  print(type(t)) #let's see the etiquettes
  print(len(training_iterable))
  print (t[1])
  print(len(t))
  print(type(t[0]))
  print(t[0].size())
  break

#here we need to build the actual neural network

class FeedForwardNN (torch.nn.Module):
  def __init__(self, input_layer, hidden_layer, output_layer):

    super(FeedForwardNN, self).__init__()

    self.h1 = torch.nn.Linear(
        in_features = input_layer,
        out_features = hidden_layer,
        bias = True
    )

    self.sigmoid = torch.nn.Sigmoid()

    self.h2 = torch.nn.Linear(
        in_features = hidden_layer,
        out_features = output_layer,
        bias = True
    )

    torch.nn.init.zeros_(self.h1.bias)
    torch.nn.init.zeros_(self.h2.bias)

  def forward(self, x):

    x = x.view(x.shape[0],-1) #this reshapes the matrix in a vector

    x = self.h1(x)
    x = self.sigmoid(x)
    x = self.h2(x)

    return x

#now we want to build an optimizer using the basic SGD

def get_optimizer (net, lr = 0.1, wd = 0.1, momentum = 0):

  optimizer = torch.optim.SGD(
      net.parameters(),
      lr = lr,
      weight_decay = wd,
      momentum = momentum,
  )

  return optimizer

#here we can build the loss function, that is the Cross Entropy one

def get_cost_function ():
  cost_function = torch.nn.CrossEntropyLoss()
  return cost_function #very straight forward

#training and test function

def training_step (net, data_loader, optimizer, cost_function, device = "cpu"):

  number_of_samples = 0.
  cumulative_loss = 0.
  cumulative_accuracy = 0.

  net.train()

  for batch_idx, (inputs, targets) in enumerate(data_loader): #in each batch we look at inputs and targets

    inputs, targets = inputs.to(device), targets.to(device)

    #now let's build the training chain

    #pass the data in the model

    outputs = net(inputs)

    #compute cost

    loss = cost_function(outputs, targets)

    #save the weights for each batch

    loss.backward()

    #run the descent

    optimizer.step()

    #set back grad parameters to 0

    optimizer.zero_grad()

    number_of_samples = number_of_samples + inputs.shape[0]
    cumulative_loss = cumulative_loss + loss.item() #sums the loss of each batch
    _, predicted = outputs.max(dim=1)
    cumulative_accuracy = cumulative_accuracy + predicted.eq(targets).sum().item()

  return cumulative_loss/number_of_samples, cumulative_accuracy/number_of_samples*100

def test_step (net, data_loader, cost_function, device = "cpu"):

  number_of_samples = 0.
  cumulative_loss = 0.
  cumulative_accuracy = 0.

  net.eval()

  # disable gradient computation (we are only testing, we do not want our model to be modified in this step!)
  with torch.no_grad():

    for batch_idx, (inputs, targets) in enumerate(data_loader): #in each batch we look at inputs and targets

      inputs, targets = inputs.to(device), targets.to(device)

      #now let's build the test chain, substantially we remove the optimizations

      outputs = net(inputs)
      loss = cost_function(outputs, targets)

      number_of_samples = number_of_samples + inputs.shape[0]
      cumulative_loss = cumulative_loss + loss.item()
      _, predicted = outputs.max(dim=1)
      cumulative_accuracy = cumulative_accuracy + predicted.eq(targets).sum().item()

    return cumulative_loss/number_of_samples, cumulative_accuracy/number_of_samples*100

#here we pack everything together with a last main function

def main(batch_size = 128,
         input_dim = 28*28,
         hidden_dim =100,
         output_dim = 10,
         device = "cpu",
         learning_rate = 0.01,
         weight_decay = 0.000001,
         momentum = 0.9,
         epochs = 10):

  training_iterable, validation_iterable, test_iterable = Dataset(batch_size)
  net = FeedForwardNN(input_dim, hidden_dim, output_dim)
  net = net.to(device)
  optimizer = get_optimizer(net, learning_rate, weight_decay, momentum)
  cost_function = get_cost_function()

  print ("before training:")

  train_loss, train_accuracy = test_step(net, training_iterable, cost_function,)
  val_loss, val_accuracy = test_step(net, validation_iterable, cost_function,)
  test_loss, test_accuracy = test_step(net, test_iterable, cost_function,)

  print ("\t Training loss{:.5f}, Training accuracy{:.2f}" .format(train_loss, train_accuracy))
  print ("\t Validation loss{:.5f}, Validation accuracy{:.2f}" .format(val_loss, val_accuracy))
  print ("\t Test loss{:.5f}, Test accuracy{:.2f}" .format(test_loss, test_accuracy))
  print ("________________________")


  #now we do the actual training

  for e in range(epochs):
    training_step(net, training_iterable, optimizer, cost_function, device)
    train_loss, train_accuracy = test_step(net, training_iterable, cost_function,)
    val_loss, val_accuracy = test_step(net, validation_iterable, cost_function,)
    print ("Epoch:{:d}".format(e+1))
    print ("\t Training loss {:.5f}, Training accuracy {:.2f}" .format(train_loss, train_accuracy))
    print ("\t Validation loss {:.5f}, Validation accuracy {:.2f}" .format(val_loss, val_accuracy))
    print ("________________________")

  #final performance

  print ("after training:")

  train_loss, train_accuracy = test_step(net, training_iterable, cost_function,)
  val_loss, val_accuracy = test_step(net, validation_iterable, cost_function,)
  test_loss, test_accuracy = test_step(net, test_iterable, cost_function,)

  print ("\t Training loss {:.5f}, Training accuracy {:.2f}" .format(train_loss, train_accuracy))
  print ("\t Validation loss {:.5f}, Validation accuracy {:.2f}" .format(val_loss, val_accuracy))
  print ("\t Test loss {:.5f}, Test accuracy {:.2f}" .format(test_loss, test_accuracy))
  print ("________________________")

! rm -rf runs

main()