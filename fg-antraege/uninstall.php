<?php
defined('WP_UNINSTALL_PLUGIN') || exit;
delete_option('fg_antraege_version');
// Alle Daten löschen - auskommentiert zum Schutz vor versehentlichem Datenverlust
// $posts = get_posts(['post_type' => 'fg_antrag', 'numberposts' => -1, 'post_status' => 'any']);
// foreach ($posts as $post) { wp_delete_post($post->ID, true); }
