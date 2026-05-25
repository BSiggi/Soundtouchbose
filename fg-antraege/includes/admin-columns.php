<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function fg_antraege_admin_columns( $columns ) {
	$columns['fg_status'] = __( 'Status', 'fg-antraege' );
	$columns['fg_datum']  = __( 'Datum', 'fg-antraege' );
	$columns['fg_pdf']    = __( 'PDF', 'fg-antraege' );
	return $columns;
}

function fg_antraege_admin_column_content( $column, $post_id ) {
	if ( 'fg_status' === $column ) {
		$status = (string) get_post_meta( $post_id, '_fg_antrag_status', true );
		if ( '' === $status ) {
			$status = 'eingereicht';
		}
		echo esc_html( fg_antraege_label_for_status( $status ) );
	}

	if ( 'fg_datum' === $column ) {
		echo esc_html( (string) get_post_meta( $post_id, '_fg_antrag_datum', true ) );
	}

	if ( 'fg_pdf' === $column ) {
		$pdf_url = (string) get_post_meta( $post_id, '_fg_antrag_pdf_url', true );
		if ( '' !== $pdf_url ) {
			echo '<a href="' . esc_url( $pdf_url ) . '" target="_blank" rel="noopener noreferrer">' . esc_html__( 'Link', 'fg-antraege' ) . '</a>';
		} else {
			echo '&mdash;';
		}
	}
}

add_filter( 'manage_fg_antrag_posts_columns', 'fg_antraege_admin_columns' );
add_action( 'manage_fg_antrag_posts_custom_column', 'fg_antraege_admin_column_content', 10, 2 );
