import numpy as np
import tensorflow as tf
from tensorboard.plugins.beholder import Beholder, im_util


def gaussian_noise_layer(input_layer, std):
    noise = tf.random_normal(shape=tf.shape(input_layer), mean=0.0, stddev=std, dtype=tf.float32)
    return input_layer + noise


def gallery(array, ncols=3):
    nindex, height, width, intensity = array.shape
    nrows = nindex//ncols
    assert nindex == nrows*ncols
    # want result.shape = (height*nrows, width*ncols, intensity)
    result = (array.reshape(nrows, ncols, height, width, intensity)
              .swapaxes(1,2)
              .reshape(height*nrows, width*ncols, intensity))
    return result

def make_array(img):
    return np.array([img]*12)


class TemporalBeholder(Beholder):
    def _get_final_image(self, session, config, arrays=None, frame=None):
        if config['values'] == 'frames':
            if frame is None:
                final_image = im_util.get_image_relative_to_script('frame-missing.png')
            else:
                frame = frame() if callable(frame) else frame
                final_image = im_util.scale_image_for_display(frame)

        elif config['values'] == 'arrays':
            if arrays is None:
                final_image = im_util.get_image_relative_to_script('arrays-missing.png')
                # TODO: hack to clear the info. Should be cleaner.
                self.visualizer._save_section_info([], [])
            else:
                final_image = self.visualizer.build_frame(arrays)

        elif config['values'] == 'trainable_variables':
            arrays = session.run(tf.trainable_variables())
            for i, ar in enumerate(arrays):
                if (len(ar.shape) == 5
                        and ar.shape[0] == 1):
                    arrays[i] = ar[0]

            final_image = self.visualizer.build_frame(arrays)

        if len(final_image.shape) == 2:
            # Map grayscale images to 3D tensors.
            final_image = np.expand_dims(final_image, -1)

        return final_image
