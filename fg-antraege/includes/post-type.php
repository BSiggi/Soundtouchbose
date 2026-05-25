<?php
/**
 * Custom Post Type: fg_antrag
 *
 * @package FG_Antraege
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register the fg_antrag custom post type.
 */
function fg_antraege_register_post_type() {
	$labels = array(
		'name'               => __( 'Anträge', 'fg-antraege' ),
		'singular_name'      => __( 'Antrag', 'fg-antraege' ),
		'add_new'            => __( 'Neuer Antrag', 'fg-antraege' ),
		'add_new_item'       => __( 'Neuen Antrag hinzufügen', 'fg-antraege' ),
		'edit_item'          => __( 'Antrag bearbeiten', 'fg-antraege' ),
		'new_item'           => __( 'Neuer Antrag', 'fg-antraege' ),
		'view_item'          => __( 'Antrag ansehen', 'fg-antraege' ),
		'search_items'       => __( 'Anträge suchen', 'fg-antraege' ),
		'not_found'          => __( 'Keine Anträge gefunden', 'fg-antraege' ),
		'not_found_in_trash' => __( 'Keine Anträge im Papierkorb', 'fg-antraege' ),
		'menu_name'          => __( 'Anträge', 'fg-antraege' ),
	);

	$args = array(
		'labels'              => $labels,
		'public'              => true,
		'show_ui'             => true,
		'show_in_menu'        => true,
		'menu_icon'           => 'dashicons-clipboard',
		'menu_position'       => 25,
		'supports'            => array( 'title', 'editor' ),
		'has_archive'         => false,
		'rewrite'             => array( 'slug' => 'antraege' ),
		'show_in_rest'        => false,
		'capability_type'     => 'post',
	);

	register_post_type( 'fg_antrag', $args );
}
add_action( 'init', 'fg_antraege_register_post_type' );
