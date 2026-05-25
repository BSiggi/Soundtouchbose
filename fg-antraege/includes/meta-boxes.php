<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function fg_antraege_add_meta_boxes() {
	add_meta_box(
		'fg_antraege_details',
		__( 'Antragsdetails', 'fg-antraege' ),
		'fg_antraege_render_meta_box',
		'fg_antrag',
		'normal',
		'default'
	);
}

function fg_antraege_render_meta_box( $post ) {
	wp_nonce_field( 'fg_antraege_save_meta', 'fg_antraege_meta_nonce' );

	$status      = get_post_meta( $post->ID, '_fg_antrag_status', true );
	$pdf_url     = get_post_meta( $post->ID, '_fg_antrag_pdf_url', true );
	$request_day = get_post_meta( $post->ID, '_fg_antrag_datum', true );
	$summary     = get_post_meta( $post->ID, '_fg_antrag_summary', true );
	?>
	<p>
		<label for="fg_antrag_status"><strong><?php esc_html_e( 'Status', 'fg-antraege' ); ?></strong></label><br />
		<select id="fg_antrag_status" name="fg_antrag_status">
			<option value="eingereicht" <?php selected( $status, 'eingereicht' ); ?>><?php esc_html_e( 'Eingereicht', 'fg-antraege' ); ?></option>
			<option value="angenommen" <?php selected( $status, 'angenommen' ); ?>><?php esc_html_e( 'Angenommen', 'fg-antraege' ); ?></option>
			<option value="abgelehnt" <?php selected( $status, 'abgelehnt' ); ?>><?php esc_html_e( 'Abgelehnt', 'fg-antraege' ); ?></option>
		</select>
	</p>
	<p>
		<label for="fg_antrag_datum"><strong><?php esc_html_e( 'Antragsdatum', 'fg-antraege' ); ?></strong></label><br />
		<input type="date" id="fg_antrag_datum" name="fg_antrag_datum" value="<?php echo esc_attr( $request_day ); ?>" />
	</p>
	<p>
		<label for="fg_antrag_pdf_url"><strong><?php esc_html_e( 'PDF-URL', 'fg-antraege' ); ?></strong></label><br />
		<input type="url" id="fg_antrag_pdf_url" name="fg_antrag_pdf_url" value="<?php echo esc_attr( $pdf_url ); ?>" class="widefat" placeholder="https://..." />
	</p>
	<p>
		<label for="fg_antrag_summary"><strong><?php esc_html_e( 'Kurzbeschreibung (ausklappbar)', 'fg-antraege' ); ?></strong></label><br />
		<textarea id="fg_antrag_summary" name="fg_antrag_summary" rows="4" class="widefat"><?php echo esc_textarea( $summary ); ?></textarea>
	</p>
	<?php
}

function fg_antraege_save_meta_boxes( $post_id ) {
	if ( ! isset( $_POST['fg_antraege_meta_nonce'] ) ) {
		return;
	}

	if ( ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['fg_antraege_meta_nonce'] ) ), 'fg_antraege_save_meta' ) ) {
		return;
	}

	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}

	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	$allowed_status = fg_antraege_allowed_statuses();
	$status         = isset( $_POST['fg_antrag_status'] ) ? sanitize_key( wp_unslash( $_POST['fg_antrag_status'] ) ) : 'eingereicht';
	if ( ! in_array( $status, $allowed_status, true ) ) {
		$status = 'eingereicht';
	}

	$request_day = isset( $_POST['fg_antrag_datum'] ) ? sanitize_text_field( wp_unslash( $_POST['fg_antrag_datum'] ) ) : '';
	if ( '' !== $request_day ) {
		$date = DateTime::createFromFormat( 'Y-m-d', $request_day );
		if ( false === $date || $request_day !== $date->format( 'Y-m-d' ) ) {
			$request_day = '';
		}
	}
	$pdf_url     = isset( $_POST['fg_antrag_pdf_url'] ) ? esc_url_raw( wp_unslash( $_POST['fg_antrag_pdf_url'] ) ) : '';
	$summary     = isset( $_POST['fg_antrag_summary'] ) ? sanitize_textarea_field( wp_unslash( $_POST['fg_antrag_summary'] ) ) : '';

	update_post_meta( $post_id, '_fg_antrag_status', $status );
	update_post_meta( $post_id, '_fg_antrag_datum', $request_day );
	update_post_meta( $post_id, '_fg_antrag_pdf_url', $pdf_url );
	update_post_meta( $post_id, '_fg_antrag_summary', $summary );
}

add_action( 'add_meta_boxes', 'fg_antraege_add_meta_boxes' );
add_action( 'save_post_fg_antrag', 'fg_antraege_save_meta_boxes' );
