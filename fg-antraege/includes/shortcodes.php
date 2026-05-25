<?php
defined('ABSPATH') || exit;

add_action('wp_enqueue_scripts', 'fg_antraege_enqueue');
add_shortcode('fg_antraege_counter', 'fg_antraege_counter_shortcode');
add_shortcode('fg_antraege_liste',   'fg_antraege_liste_shortcode');

function fg_antraege_enqueue() {
    wp_enqueue_style('fg-antraege', FG_ANTRAEGE_URL . 'assets/fg-antraege.css', [], FG_ANTRAEGE_VERSION);
    wp_enqueue_script('fg-antraege', FG_ANTRAEGE_URL . 'assets/fg-antraege.js', [], FG_ANTRAEGE_VERSION, true);
}

function fg_antraege_get_counts() {
    $counts = ['gesamt' => 0, 'angenommen' => 0, 'abgelehnt' => 0, 'eingereicht' => 0];
    $posts = get_posts(['post_type' => 'fg_antrag', 'numberposts' => -1, 'post_status' => 'publish']);
    foreach ($posts as $post) {
        $status = get_post_meta($post->ID, '_fg_antrag_status', true) ?: 'eingereicht';
        $counts['gesamt']++;
        if (isset($counts[$status])) $counts[$status]++;
    }
    return $counts;
}

function fg_antraege_counter_shortcode() {
    $c = fg_antraege_get_counts();
    ob_start(); ?>
    <div class="fg-antraege-counter">
        <div class="fg-counter-box">
            <span class="fg-counter-zahl"><?php echo esc_html($c['gesamt']); ?></span>
            <span class="fg-counter-label">Anträge gesamt</span>
        </div>
        <div class="fg-counter-box">
            <span class="fg-counter-zahl fg-color-angenommen"><?php echo esc_html($c['angenommen']); ?></span>
            <span class="fg-counter-label">Angenommen</span>
        </div>
        <div class="fg-counter-box">
            <span class="fg-counter-zahl fg-color-abgelehnt"><?php echo esc_html($c['abgelehnt']); ?></span>
            <span class="fg-counter-label">Abgelehnt</span>
        </div>
        <div class="fg-counter-box">
            <span class="fg-counter-zahl fg-color-eingereicht"><?php echo esc_html($c['eingereicht']); ?></span>
            <span class="fg-counter-label">Eingereicht</span>
        </div>
    </div>
    <?php return ob_get_clean();
}

function fg_antraege_liste_shortcode() {
    $posts = get_posts(['post_type' => 'fg_antrag', 'numberposts' => -1, 'post_status' => 'publish', 'orderby' => 'date', 'order' => 'DESC']);
    ob_start(); ?>
    <div class="fg-antraege-liste">
        <div class="fg-filter-buttons">
            <button class="fg-filter-btn active" data-filter="alle">Alle</button>
            <button class="fg-filter-btn" data-filter="angenommen">Angenommen</button>
            <button class="fg-filter-btn" data-filter="abgelehnt">Abgelehnt</button>
            <button class="fg-filter-btn" data-filter="eingereicht">Eingereicht</button>
        </div>
        <?php foreach ($posts as $post):
            $status  = get_post_meta($post->ID, '_fg_antrag_status', true) ?: 'eingereicht';
            $datum   = get_post_meta($post->ID, '_fg_antrag_datum', true);
            $pdf_url = get_post_meta($post->ID, '_fg_antrag_pdf', true);
            $inhalt  = apply_filters('the_content', $post->post_content);
            $datum_f = $datum ? date_i18n('d.m.Y', strtotime($datum)) : '';
            $status_labels = ['angenommen' => 'Angenommen ✓', 'abgelehnt' => 'Abgelehnt ✗', 'eingereicht' => 'Eingereicht'];
            $status_label  = $status_labels[$status] ?? 'Eingereicht';
        ?>
        <div class="fg-antrag-item" data-status="<?php echo esc_attr($status); ?>">
            <div class="fg-antrag-header">
                <span class="fg-antrag-titel"><?php echo esc_html($post->post_title); ?></span>
                <span class="fg-status-badge fg-status-<?php echo esc_attr($status); ?>"><?php echo esc_html($status_label); ?></span>
                <?php if ($datum_f): ?><span class="fg-antrag-datum"><?php echo esc_html($datum_f); ?></span><?php endif; ?>
                <span class="fg-accordion-toggle">▶</span>
            </div>
            <div class="fg-antrag-body">
                <?php if ($inhalt): echo wp_kses_post($inhalt); endif; ?>
                <?php if ($pdf_url): ?>
                <a href="<?php echo esc_url($pdf_url); ?>" class="fg-pdf-btn" target="_blank" rel="noopener">📄 PDF herunterladen</a>
                <?php endif; ?>
            </div>
        </div>
        <?php endforeach; ?>
    </div>
    <?php return ob_get_clean();
}
