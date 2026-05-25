<?php
defined('ABSPATH') || exit;

add_action('init', 'fg_antraege_register_post_type');

function fg_antraege_register_post_type() {
    $labels = [
        'name'               => 'Anträge',
        'singular_name'      => 'Antrag',
        'add_new'            => 'Neuer Antrag',
        'add_new_item'       => 'Neuen Antrag hinzufügen',
        'edit_item'          => 'Antrag bearbeiten',
        'new_item'           => 'Neuer Antrag',
        'view_item'          => 'Antrag ansehen',
        'search_items'       => 'Anträge suchen',
        'not_found'          => 'Keine Anträge gefunden',
        'not_found_in_trash' => 'Keine Anträge im Papierkorb',
        'menu_name'          => 'Anträge',
    ];
    register_post_type('fg_antrag', [
        'labels'        => $labels,
        'public'        => true,
        'has_archive'   => false,
        'show_in_menu'  => true,
        'menu_icon'     => 'dashicons-clipboard',
        'supports'      => ['title', 'editor'],
        'rewrite'       => ['slug' => 'antraege'],
        'show_in_rest'  => false,
    ]);
}
