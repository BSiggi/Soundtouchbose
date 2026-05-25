<?php
defined('ABSPATH') || exit;

add_action('add_meta_boxes', 'fg_antraege_add_meta_boxes');
add_action('save_post_fg_antrag', 'fg_antraege_save_meta');

function fg_antraege_add_meta_boxes() {
    add_meta_box('fg_antrag_details', 'Antrags-Details', 'fg_antraege_meta_box_html', 'fg_antrag', 'normal', 'high');
}

function fg_antraege_meta_box_html($post) {
    wp_nonce_field('fg_antrag_save', 'fg_antrag_nonce');
    $status  = get_post_meta($post->ID, '_fg_antrag_status', true) ?: 'eingereicht';
    $datum   = get_post_meta($post->ID, '_fg_antrag_datum', true);
    $pdf_url = get_post_meta($post->ID, '_fg_antrag_pdf', true);
    ?>
    <table class="form-table">
        <tr>
            <th><label for="fg_antrag_status">Status</label></th>
            <td>
                <select name="fg_antrag_status" id="fg_antrag_status">
                    <option value="eingereicht" <?php selected($status, 'eingereicht'); ?>>Eingereicht</option>
                    <option value="angenommen"  <?php selected($status, 'angenommen');  ?>>Angenommen ✓</option>
                    <option value="abgelehnt"   <?php selected($status, 'abgelehnt');   ?>>Abgelehnt ✗</option>
                </select>
            </td>
        </tr>
        <tr>
            <th><label for="fg_antrag_datum">Datum (YYYY-MM-DD)</label></th>
            <td><input type="date" name="fg_antrag_datum" id="fg_antrag_datum" value="<?php echo esc_attr($datum); ?>" /></td>
        </tr>
        <tr>
            <th><label for="fg_antrag_pdf">PDF-URL</label></th>
            <td>
                <input type="url" name="fg_antrag_pdf" id="fg_antrag_pdf" value="<?php echo esc_url($pdf_url); ?>" style="width:70%" />
                <button type="button" class="button" id="fg_antrag_pdf_upload">PDF auswählen</button>
                <script>
                document.getElementById('fg_antrag_pdf_upload').addEventListener('click', function(e){
                    e.preventDefault();
                    var frame = wp.media({ title: 'PDF auswählen', button: { text: 'PDF verwenden' }, multiple: false });
                    frame.on('select', function(){
                        var attachment = frame.state().get('selection').first().toJSON();
                        document.getElementById('fg_antrag_pdf').value = attachment.url;
                    });
                    frame.open();
                });
                </script>
            </td>
        </tr>
    </table>
    <?php
}

function fg_antraege_save_meta($post_id) {
    if (!isset($_POST['fg_antrag_nonce']) || !wp_verify_nonce($_POST['fg_antrag_nonce'], 'fg_antrag_save')) return;
    if (!current_user_can('edit_post', $post_id)) return;
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;

    $allowed_status = ['eingereicht', 'angenommen', 'abgelehnt'];
    $status = isset($_POST['fg_antrag_status']) && in_array($_POST['fg_antrag_status'], $allowed_status)
        ? $_POST['fg_antrag_status'] : 'eingereicht';
    update_post_meta($post_id, '_fg_antrag_status', $status);
    update_post_meta($post_id, '_fg_antrag_datum',  sanitize_text_field($_POST['fg_antrag_datum'] ?? ''));
    update_post_meta($post_id, '_fg_antrag_pdf',    esc_url_raw($_POST['fg_antrag_pdf'] ?? ''));
}
