import urwid
import math
import requests
import warnings

# If term_image is loaded use their screen implementation which handles images
try:
    from term_image.widget import UrwidImageScreen, UrwidImage
    from term_image.image import BaseImage, KittyImage, ITerm2Image, BlockImage
    from term_image import disable_queries  # prevent phantom keystrokes
    from PIL import Image, ImageDraw

    _IMAGE_PIXEL_FORMATS = frozenset({'kitty', 'iterm'})
    _ImageCls = None

    TuiScreen = UrwidImageScreen
    disable_queries()

    def image_support_enabled():
        return True

    def can_render_pixels(image_format):
        return image_format in _IMAGE_PIXEL_FORMATS

    def get_base_image(image, image_format, colors) -> BaseImage:
        # we don't autodetect kitty, iterm; we choose based on option switches

        global _ImageCls

        if not _ImageCls:
            _ImageCls = (
                KittyImage
                if image_format == 'kitty'
                else ITerm2Image
                if image_format == 'iterm'
                else BlockImage
            )
            _ImageCls.forced_support = True
            if colors == 256 and not can_render_pixels(image_format):
                _ImageCls.set_render_method("INDEXED")

        return _ImageCls(image)

    def resize_image(basewidth: int, baseheight: int, img: Image.Image) -> Image.Image:
        if baseheight and not basewidth:
            hpercent = baseheight / float(img.size[1])
            width = math.ceil(img.size[0] * hpercent)
            img = img.resize((width, baseheight), Image.Resampling.LANCZOS)
        elif basewidth and not baseheight:
            wpercent = (basewidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((basewidth, hsize), Image.Resampling.LANCZOS)
        else:
            img = img.resize((basewidth, baseheight), Image.Resampling.LANCZOS)

        if img.mode != 'P':
            img = img.convert('RGB')
        return img

    def add_corners(img, rad):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', img.size, "white")
        w, h = img.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        img.putalpha(alpha)
        return img

    def load_image(url):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # suppress "corrupt exif" output from PIL
            try:
                img = Image.open(requests.get(url, stream=True).raw)
                if img.format == 'PNG' and img.mode != 'RGBA':
                    img = img.convert("RGBA")
                return img
            except Exception:
                return None

    def graphics_widget(img, image_format="block", corner_radius=0, colors=16777216) -> urwid.Widget:
        if not img:
            return urwid.SolidFill(fill_char=" ")

        if can_render_pixels(image_format) and corner_radius > 0:
            render_img = add_corners(img, 10)
        else:
            render_img = img

        return UrwidImage(get_base_image(render_img, image_format, colors), '<', upscale=True)
        # "<" means left-justify the image

except ImportError:
    from urwid.raw_display import Screen
    TuiScreen = Screen

    def image_support_enabled():
        return False

    def can_render_pixels(image_format: str):
        return False

    def get_base_image(image, image_format: str):
        return None

    def add_corners(img, rad):
        return None

    def load_image(url):
        return None

    def graphics_widget(img, image_format="block", corner_radius=0) -> urwid.Widget:
        return urwid.SolidFill(fill_char=" ")
