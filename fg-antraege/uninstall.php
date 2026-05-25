<?php
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
	exit;
}

$posts = get_posts(
	array(
		'post_type'      => 'fg_antrag',
		'post_status'    => 'any',
		'posts_per_page' => -1,
		'fields'         => 'ids',
	)
);

if ( ! empty( $posts ) ) {
	foreach ( $posts as $post_id ) {
		wp_delete_post( (int) $post_id, true );
	}
}
