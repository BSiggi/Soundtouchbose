<?php
/**
 * Plugin Name: FG Anträge
 * Description: Verwaltung und Ausgabe von Stadtratsanträgen mit Zähler- und Listen-Shortcodes.
 * Version: 1.0.0
 * Author: FG
 * Requires at least: 6.0
 * Requires PHP: 7.4
 * Text Domain: fg-antraege
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'FG_ANTRAEGE_VERSION', '1.0.0' );
define( 'FG_ANTRAEGE_DIR', plugin_dir_path( __FILE__ ) );
define( 'FG_ANTRAEGE_URL', plugin_dir_url( __FILE__ ) );

require_once FG_ANTRAEGE_DIR . 'includes/post-type.php';
require_once FG_ANTRAEGE_DIR . 'includes/meta-boxes.php';
require_once FG_ANTRAEGE_DIR . 'includes/shortcodes.php';
require_once FG_ANTRAEGE_DIR . 'includes/admin-columns.php';

function fg_antraege_activate() {
	fg_antraege_register_post_type();
	flush_rewrite_rules();
}

function fg_antraege_deactivate() {
	flush_rewrite_rules();
}

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

register_activation_hook( __FILE__, 'fg_antraege_activate' );
register_deactivation_hook( __FILE__, 'fg_antraege_deactivate' );
add_action( 'wp_enqueue_scripts', 'fg_antraege_enqueue_assets' );
