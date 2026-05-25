<?php
/**
 * Plugin Name: FG Anträge
 * Plugin URI: https://friedliches-geiselhoering.de
 * Description: Stadtrats-Anträge verwalten und auf der Website anzeigen
 * Version: 1.0.0
 * Author: Friedliches Geiselhöring
 * Text Domain: fg-antraege
 * Requires at least: 6.0
 * Tested up to: 6.8
 * Requires PHP: 7.4
 */
defined('ABSPATH') || exit;

define('FG_ANTRAEGE_VERSION', '1.0.0');
define('FG_ANTRAEGE_PATH', plugin_dir_path(__FILE__));
define('FG_ANTRAEGE_URL', plugin_dir_url(__FILE__));

require_once FG_ANTRAEGE_PATH . 'includes/post-type.php';
require_once FG_ANTRAEGE_PATH . 'includes/meta-boxes.php';
require_once FG_ANTRAEGE_PATH . 'includes/shortcodes.php';
require_once FG_ANTRAEGE_PATH . 'includes/admin-columns.php';

register_activation_hook(__FILE__, 'fg_antraege_activate');
register_deactivation_hook(__FILE__, 'fg_antraege_deactivate');

function fg_antraege_activate() {
    if (version_compare(get_bloginfo('version'), '6.0', '<')) {
        deactivate_plugins(plugin_basename(__FILE__));
        wp_die('FG Anträge benötigt WordPress 6.0 oder höher.');
    }
    fg_antraege_register_post_type();
    flush_rewrite_rules();
    update_option('fg_antraege_version', FG_ANTRAEGE_VERSION);
}

function fg_antraege_deactivate() {
    flush_rewrite_rules();
}
