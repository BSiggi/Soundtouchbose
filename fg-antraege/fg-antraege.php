<?php
/**
 * Plugin Name: FG Anträge
 * Plugin URI:  https://friedliches-geiselhoering.de
 * Description: Stadtrats-Anträge verwalten und auf der Website anzeigen
 * Version:     1.0.0
 * Author:      Friedliches Geiselhöring
 * Text Domain: fg-antraege
 * License:     GPL-2.0-or-later
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'FG_ANTRAEGE_VERSION', '1.0.0' );
define( 'FG_ANTRAEGE_DIR', plugin_dir_path( __FILE__ ) );
define( 'FG_ANTRAEGE_URL', plugin_dir_url( __FILE__ ) );

require_once FG_ANTRAEGE_DIR . 'includes/post-type.php';
require_once FG_ANTRAEGE_DIR . 'includes/meta-boxes.php';
require_once FG_ANTRAEGE_DIR . 'includes/admin-columns.php';
require_once FG_ANTRAEGE_DIR . 'includes/shortcodes.php';

/**
 * Enqueue frontend assets.
 */
function fg_antraege_enqueue_assets() {
	wp_enqueue_style(
		'fg-antraege',
		FG_ANTRAEGE_URL . 'assets/fg-antraege.css',
		array(),
		FG_ANTRAEGE_VERSION
	);
	wp_enqueue_script(
		'fg-antraege',
		FG_ANTRAEGE_URL . 'assets/fg-antraege.js',
		array(),
		FG_ANTRAEGE_VERSION,
		true
	);
}
add_action( 'wp_enqueue_scripts', 'fg_antraege_enqueue_assets' );

/**
 * Plugin activation: flush rewrite rules.
 */
function fg_antraege_activate() {
	fg_antraege_register_post_type();
	flush_rewrite_rules();
}
register_activation_hook( __FILE__, 'fg_antraege_activate' );

/**
 * Plugin deactivation: flush rewrite rules.
 */
function fg_antraege_deactivate() {
	flush_rewrite_rules();
}
register_deactivation_hook( __FILE__, 'fg_antraege_deactivate' );
