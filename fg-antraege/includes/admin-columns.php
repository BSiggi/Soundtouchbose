<?php

defined( 'ABSPATH' ) || exit;

/**
 * Admin-Spalten erweitern.
 *
 * @param array $columns Spalten.
 * @return array
 */
function fg_antraege_admin_columns( $columns ) {
	$columns['fg_status'] = __( 'Status', 'fg-antraege' );
	$columns['fg_pdf']    = __( 'PDF', 'fg-antraege' );
	return $columns;
}
add_filter( 'manage_fg_antrag_posts_columns', 'fg_antraege_admin_columns' );

/**
 * Admin-Spalten befüllen.
 *
 * @param string $column  Spalte.
 * @param int    $post_id Post-ID.
 * @return void
 */
function fg_antraege_render_admin_columns( $column, $post_id ) {
	if ( 'fg_status' === $column ) {
		$status = get_post_meta( $post_id, '_fg_status', true );
		echo esc_html( $status ? ucfirst( $status ) : __( 'Eingereicht', 'fg-antraege' ) );
	}

	if ( 'fg_pdf' === $column ) {
		$pdf_url = get_post_meta( $post_id, '_fg_pdf_url', true );
		if ( ! empty( $pdf_url ) ) {
			echo '<a href="' . esc_url( $pdf_url ) . '" target="_blank" rel="noopener noreferrer">' . esc_html__( 'PDF', 'fg-antraege' ) . '</a>';
		} else {
			echo esc_html__( '—', 'fg-antraege' );
		}
	}
}
add_action( 'manage_fg_antrag_posts_custom_column', 'fg_antraege_render_admin_columns', 10, 2 );
