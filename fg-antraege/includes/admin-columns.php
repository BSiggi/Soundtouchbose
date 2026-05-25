<?php
defined('ABSPATH') || exit;

add_filter('manage_fg_antrag_posts_columns',       'fg_antraege_columns');
add_action('manage_fg_antrag_posts_custom_column', 'fg_antraege_column_content', 10, 2);

function fg_antraege_columns($columns) {
    $new = [];
    foreach ($columns as $key => $val) {
        $new[$key] = $val;
        if ($key === 'title') {
            $new['fg_status'] = 'Status';
            $new['fg_datum']  = 'Datum';
            $new['fg_pdf']    = 'PDF';
        }
    }
    return $new;
}

function fg_antraege_column_content($column, $post_id) {
    if ($column === 'fg_status') {
        $status = get_post_meta($post_id, '_fg_antrag_status', true) ?: 'eingereicht';
        $colors = ['angenommen' => '#28a745', 'abgelehnt' => '#dc3545', 'eingereicht' => '#F5A623'];
        $labels = ['angenommen' => 'Angenommen ✓', 'abgelehnt' => 'Abgelehnt ✗', 'eingereicht' => 'Eingereicht'];
        $color  = $colors[$status] ?? '#F5A623';
        $label  = $labels[$status] ?? 'Eingereicht';
        echo '<span style="background:' . esc_attr($color) . ';color:#fff;padding:2px 8px;border-radius:3px;font-size:12px;">' . esc_html($label) . '</span>';
    }
    if ($column === 'fg_datum') {
        $datum = get_post_meta($post_id, '_fg_antrag_datum', true);
        echo $datum ? esc_html(date_i18n('d.m.Y', strtotime($datum))) : '—';
    }
    if ($column === 'fg_pdf') {
        $pdf = get_post_meta($post_id, '_fg_antrag_pdf', true);
        echo $pdf ? '<a href="' . esc_url($pdf) . '" target="_blank">📄 PDF</a>' : '—';
    }
}
