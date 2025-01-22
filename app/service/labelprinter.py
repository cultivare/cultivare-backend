# git+https://github.com/cultivare/brother_ql.git

from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster

from app.config import settings

from PIL import Image, ImageDraw, ImageFont
import qrcode


def print_image(im):
    backend = settings.PRINTER_BACKEND  # 'pyusb', 'linux_kernal', 'network'
    model = settings.PRINTER_MODEL # your printer model.
    printer = settings.PRINTER_ADDRESS  # Get these values from the Windows usb driver filter.  Linux/Raspberry Pi uses '/dev/usb/lp0'.

    qlr = BrotherQLRaster(model)
    qlr.exception_on_warning = True

    instructions = convert(
        qlr=qlr,
        images=[im],  #  Takes a list of file names or PIL objects.
        label=str(settings.PRINTER_LABEL_SIZE),
        rotate="0",  # 'Auto', '0', '90', '270'
        threshold=70.0,  # Black and white threshold in percent.
        dither=False,
        compress=False,
        red=False,  # Only True if using Red/Black 62 mm label tape.
        dpi_600=True,
        hq=True,  # False for low quality.
        cut=True,
    )

    send(
        instructions=instructions,
        printer_identifier=printer,
        backend_identifier=backend,
        blocking=True,
    )


def create_label_image(
    print_data,
    qr_size=284,
    font_sizes=[70, 55, 55, 45],
    image_height=284,
    qr_position=(0, 0),
    text_position=(350, 0),
    text_color="black",
    qr_color="black",
    background_color="white",
    line_spacing=5,
    min_width=900,
):
    """
    Generates a label image with a QR code and text based on the PrintData.
    """

    # Prepare text lines
    text_lines = [
        print_data.labelText,
        print_data.dateText,
        print_data.noteText or "",  # Handle optional noteText
        "[ for microscopy use only ]" if print_data.RestrictiveLabel else "",
    ]

    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=0)
    qr.add_data(print_data.barcodeText)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=qr_color, back_color="white").resize(
        (qr_size, qr_size)
    )

    # Calculate text width
    total_text_width = 0
    font = ImageFont.load_default()
    for i, line in enumerate(text_lines):
        font = font.font_variant(size=font_sizes[i])
        bbox = font.getbbox(line)
        total_text_width = max(total_text_width, bbox[2])

    # Calculate image width
    image_width = max(min_width, text_position[0] + total_text_width + 20)

    # Create a new image
    img = Image.new("RGB", (image_width, image_height), background_color)
    draw = ImageDraw.Draw(img)

    # Paste QR code
    img.paste(qr_img, qr_position)

    # Add text
    y = text_position[1]
    for i, line in enumerate(text_lines):
        font = ImageFont.load_default()
        font = font.font_variant(size=font_sizes[i])
        if i == 0:  # Make the first line bold
            try:
                bold_font = font.getmask(line, "1")
                draw.text((text_position[0], y), line, font=bold_font, fill=text_color)
            except:
                draw.text((text_position[0], y), line, font=font, fill=text_color)
        else:
            draw.text((text_position[0], y), line, font=font, fill=text_color)

        bbox = font.getbbox(line)
        y += bbox[3] + line_spacing

    # Save the image
    return img  # img.save(output_filename)


def print_label(print_data):
    print(print_data)
    img = create_label_image(print_data)
    img = img.rotate(90, expand=True)
    print_image(img)
    return True
