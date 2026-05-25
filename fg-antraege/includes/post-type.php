<?php

defined( 'ABSPATH' ) || exit;

/**
 * Registriert den Custom Post Type für Anträge.
 *
 * @return void
 */
function fg_antraege_register_post_type() {
	$labels = array(
		'name'               => __( 'Anträge', 'fg-antraege' ),
		'singular_name'      => __( 'Antrag', 'fg-antraege' ),
		'add_new'            => __( 'Neu hinzufügen', 'fg-antraege' ),
		'add_new_item'       => __( 'Neuen Antrag erstellen', 'fg-antraege' ),
		'edit_item'          => __( 'Antrag bearbeiten', 'fg-antraege' ),
		'new_item'           => __( 'Neuer Antrag', 'fg-antraege' ),
		'view_item'          => __( 'Antrag ansehen', 'fg-antraege' ),
		'search_items'       => __( 'Anträge suchen', 'fg-antraege' ),
		'not_found'          => __( 'Keine Anträge gefunden', 'fg-antraege' ),
		'not_found_in_trash' => __( 'Keine Anträge im Papierkorb', 'fg-antraege' ),
		'menu_name'          => __( 'Anträge', 'fg-antraege' ),
	);

	register_post_type(
		'fg_antrag',
		array(
			'labels'             => $labels,
			'public'             => true,
			'show_in_rest'       => true,
			'has_archive'        => true,
			'rewrite'            => array( 'slug' => 'antraege' ),
			'menu_icon'          => 'dashicons-media-document',
			'supports'           => array( 'title', 'editor', 'excerpt' ),
			'publicly_queryable' => true,
		)
	);
}
add_action( 'init', 'fg_antraege_register_post_type' );
