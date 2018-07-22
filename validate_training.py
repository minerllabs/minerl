numpy.load('./network.npy')

matrix=numpy.genfromtxt(path,delimiter=',') # Read the numpy matrix with images in the rows
c=matrix[0]
c=c.reshape(120, 165) # this is the size of my pictures
im=plt.imshow(c)
for row in matrix:
    row=row.reshape(120, 165) # this is the size of my pictures
    im.set_data(row)
    plt.pause(0.02)
plt.show()