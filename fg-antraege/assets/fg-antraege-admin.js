/**
 * FG Anträge – Admin JavaScript
 * Handles the PDF media uploader button in the meta box.
 */

(function ($) {
    'use strict';

    if (!$) {
        return;
    }

    $('#fg_antrag_pdf_upload').on('click', function (e) {
        e.preventDefault();

        var mediaUploader = wp.media({
            title:    fgAntraegeAdmin.selectTitle,
            button:   { text: fgAntraegeAdmin.selectButton },
            multiple: false,
            library:  { type: 'application/pdf' }
        });

        mediaUploader.on('select', function () {
            var attachment = mediaUploader.state().get('selection').first().toJSON();
            $('#fg_antrag_pdf').val(attachment.url);
        });

        mediaUploader.open();
    });

}(window.jQuery));
