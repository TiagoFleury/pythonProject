import matplotlib.pyplot as plt
import PIL
import time


def fig2img(fig):
    """Convert a Matplotlib figure to a PIL Image and return it"""
    import io
    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    img = PIL.Image.open(buf)
    return img


def plot_fig(fig):
    img = fig2img(fig)
    plt.imshow(img)
    plt.show()


def figs2gif(figs, name='UCT_10000_c0.5_gt26.gif', time_by_frame=0.5):
    imgs = []
    for fig in figs:
        imgs.append(fig2img(fig))

    imgs[0].save(name, save_all=True, append_images=imgs[1:], optimize=False, loop=0,
                 duration=time_by_frame * 1000)
    return imgs


def timeit(func):
    """
    Decorator for measuring function's running time.
    """

    def measure_time(*args, **kw):
        start_time = time.perf_counter()
        result = func(*args, **kw)
        time_ms = (time.perf_counter() - start_time) * 1000
        if time_ms < 0.1:
            print("Processing time of %s(): %.1f μs."
                  % (func.__qualname__, time_ms*1000))
        else:
            print("Processing time of %s(): %.3f ms."
                  % (func.__qualname__, time_ms))
        return result

    return measure_time
