<?php
/**
 * Admin Columns for fg_antrag post type.
 *
 * @package FG_Antraege
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Define custom columns.
 *
 * @param array $columns Default columns.
 * @return array Modified columns.
 */
function fg_antraege_set_columns( $columns ) {
	$new_columns = array(
		'cb'               => $columns['cb'],
		'title'            => $columns['title'],
		'fg_antrag_status' => __( 'Status', 'fg-antraege' ),
		'fg_antrag_datum'  => __( 'Datum', 'fg-antraege' ),
		'fg_antrag_pdf'    => __( 'PDF', 'fg-antraege' ),
	);
	return $new_columns;
}
add_filter( 'manage_fg_antrag_posts_columns', 'fg_antraege_set_columns' );

/**
 * Render custom column content.
 *
 * @param string $column  Column name.
 * @param int    $post_id Post ID.
 */
function fg_antraege_render_columns( $column, $post_id ) {
	switch ( $column ) {
		case 'fg_antrag_status':
			$status = get_post_meta( $post_id, '_fg_antrag_status', true );
			$colors = array(
				'angenommen'  => '#28a745',
				'abgelehnt'   => '#dc3545',
				'eingereicht' => '#F5A623',
			);
			$labels = array(
				'angenommen'  => __( 'Angenommen', 'fg-antraege' ),
				'abgelehnt'   => __( 'Abgelehnt', 'fg-antraege' ),
				'eingereicht' => __( 'Eingereicht', 'fg-antraege' ),
			);
			$color = isset( $colors[ $status ] ) ? $colors[ $status ] : '#999';
			$label = isset( $labels[ $status ] ) ? $labels[ $status ] : esc_html( $status );
			printf(
				'<span style="display:inline-block;padding:2px 8px;border-radius:3px;background:%s;color:#fff;font-size:12px;">%s</span>',
				esc_attr( $color ),
				esc_html( $label )
			);
			break;

		case 'fg_antrag_datum':
			$datum = get_post_meta( $post_id, '_fg_antrag_datum', true );
			echo esc_html( $datum );
			break;

		case 'fg_antrag_pdf':
			$pdf = get_post_meta( $post_id, '_fg_antrag_pdf', true );
			if ( ! empty( $pdf ) ) {
				printf(
					'<a href="%s" target="_blank">%s</a>',
					esc_url( $pdf ),
					esc_html__( 'PDF ansehen', 'fg-antraege' )
				);
			} else {
				echo '—';
			}
			break;
	}
}
add_action( 'manage_fg_antrag_posts_custom_column', 'fg_antraege_render_columns', 10, 2 );

/**
 * Make status and date columns sortable.
 *
 * @param array $sortable_columns Sortable columns.
 * @return array Modified sortable columns.
 */
function fg_antraege_sortable_columns( $sortable_columns ) {
	$sortable_columns['fg_antrag_status'] = 'fg_antrag_status';
	$sortable_columns['fg_antrag_datum']  = 'fg_antrag_datum';
	return $sortable_columns;
}
add_filter( 'manage_edit-fg_antrag_sortable_columns', 'fg_antraege_sortable_columns' );
