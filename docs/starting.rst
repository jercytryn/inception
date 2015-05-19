Getting Started
==================

To get started, simply import the inception module. This should you access to most useful public methods.

.. code-block:: python

    import inception
    
Next, you say you have a filepath to a background image and a url to a foreground image,
and you know the boundingbox where you want the foreground to live relative to the upper-right corner of the background. To insert your foreground into your background image, you could simply call:

.. code-block:: python

    result = inception.inception('http://my/awesome/foreground.jpg', '/Users/mrayder/background.png', (30, 40, 300, 500))
    
Finally, you will likely wish to save your image out.  This can be accomplished by calling 

.. code-block:: python

    result.save("myawesome_composite.png")
    
`save` will automatically take care of saving out your composite in the format corresponding to your extension, similar to `PIL <http://www.pythonware.com/products/pil>`_ (in fact it's using Python Image Library under the hood)
