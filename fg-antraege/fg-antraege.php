<?php
/**
 * Plugin Name: FG Anträge
 * Description: Verwaltung und Darstellung von Stadtratsanträgen mit Status, PDF und Auswertung.
 * Version: 1.0.0
 * Author: FG
 * Requires at least: 6.0
 * Tested up to: 6.8
 * Requires PHP: 7.4
 * Text Domain: fg-antraege
 */

defined( 'ABSPATH' ) || exit;

define( 'FG_ANTRAEGE_VERSION', '1.0.0' );
define( 'FG_ANTRAEGE_PATH', plugin_dir_path( __FILE__ ) );
define( 'FG_ANTRAEGE_URL', plugin_dir_url( __FILE__ ) );

require_once FG_ANTRAEGE_PATH . 'includes/post-type.php';
require_once FG_ANTRAEGE_PATH . 'includes/meta-boxes.php';
require_once FG_ANTRAEGE_PATH . 'includes/shortcodes.php';
require_once FG_ANTRAEGE_PATH . 'includes/admin-columns.php';

/**
 * Aktivierung inkl. Versionsprüfung und Rewrite-Refresh.
 *
 * @return void
 */
function fg_antraege_activate() {
	global $wp_version;

	if ( version_compare( (string) $wp_version, '6.0', '<' ) ) {
		deactivate_plugins( plugin_basename( __FILE__ ) );
		wp_die(
			esc_html__( 'FG Anträge benötigt mindestens WordPress 6.0.', 'fg-antraege' ),
			esc_html__( 'Plugin konnte nicht aktiviert werden', 'fg-antraege' ),
			array( 'back_link' => true )
		);
	}

	if ( version_compare( PHP_VERSION, '7.4', '<' ) ) {
		deactivate_plugins( plugin_basename( __FILE__ ) );
		wp_die(
			esc_html__( 'FG Anträge benötigt mindestens PHP 7.4.', 'fg-antraege' ),
			esc_html__( 'Plugin konnte nicht aktiviert werden', 'fg-antraege' ),
			array( 'back_link' => true )
		);
	}

	fg_antraege_register_post_type();
	flush_rewrite_rules();
	fg_antraege_maybe_upgrade();
}
register_activation_hook( __FILE__, 'fg_antraege_activate' );

/**
 * Deaktivierung.
 *
 * @return void
 */
function fg_antraege_deactivate() {
	flush_rewrite_rules();
}
register_deactivation_hook( __FILE__, 'fg_antraege_deactivate' );

/**
 * Upgrade-Routine.
 *
 * @return void
 */
function fg_antraege_maybe_upgrade() {
	$installed_version = get_option( 'fg_antraege_version', '0.0.0' );

	if ( version_compare( (string) $installed_version, FG_ANTRAEGE_VERSION, '<' ) ) {
		fg_antraege_run_upgrade( (string) $installed_version );
		update_option( 'fg_antraege_version', FG_ANTRAEGE_VERSION );
	}
}

/**
 * Platzhalter für künftige Migrationen.
 *
 * @param string $from_version Installierte Version.
 * @return void
 */
function fg_antraege_run_upgrade( $from_version ) {
	// Platzhalter: künftige Migrationen auf Basis von $from_version ergänzen.
}

add_action( 'plugins_loaded', 'fg_antraege_maybe_upgrade' );
