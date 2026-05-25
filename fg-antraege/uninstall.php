<?php

defined( 'ABSPATH' ) || exit;
defined( 'WP_UNINSTALL_PLUGIN' ) || exit;
// Aufräumen bei Deinstallation.
// delete_option( 'fg_antraege_version' );
// Alle fg_antrag Posts löschen - auskommentiert damit Daten nicht versehentlich verloren gehen.
// $posts = get_posts( array( 'post_type' => 'fg_antrag', 'numberposts' => -1 ) );
// foreach ( $posts as $post ) { wp_delete_post( $post->ID, true ); }
