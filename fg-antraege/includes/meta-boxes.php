<?php

defined( 'ABSPATH' ) || exit;

/**
 * Meta-Boxen registrieren.
 *
 * @return void
 */
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
add_action( 'add_meta_boxes', 'fg_antraege_add_meta_boxes' );

/**
 * Meta-Box ausgeben.
 *
 * @param WP_Post $post Beitrag.
 * @return void
 */
function fg_antraege_render_meta_box( $post ) {
	$status  = get_post_meta( $post->ID, '_fg_status', true );
	$pdf_url = get_post_meta( $post->ID, '_fg_pdf_url', true );

	wp_nonce_field( 'fg_antraege_save_meta', 'fg_antraege_nonce' );
	?>
	<p>
		<label for="fg_status"><strong><?php echo esc_html__( 'Status', 'fg-antraege' ); ?></strong></label><br />
		<select id="fg_status" name="fg_status">
			<option value="eingereicht" <?php selected( $status, 'eingereicht' ); ?>><?php echo esc_html__( 'Eingereicht', 'fg-antraege' ); ?></option>
			<option value="angenommen" <?php selected( $status, 'angenommen' ); ?>><?php echo esc_html__( 'Angenommen', 'fg-antraege' ); ?></option>
			<option value="abgelehnt" <?php selected( $status, 'abgelehnt' ); ?>><?php echo esc_html__( 'Abgelehnt', 'fg-antraege' ); ?></option>
		</select>
	</p>
	<p>
		<label for="fg_pdf_url"><strong><?php echo esc_html__( 'PDF-URL', 'fg-antraege' ); ?></strong></label><br />
		<input type="url" id="fg_pdf_url" name="fg_pdf_url" value="<?php echo esc_attr( (string) $pdf_url ); ?>" class="widefat" />
	</p>
	<?php
}

/**
 * Meta-Box-Daten speichern.
 *
 * @param int $post_id Post-ID.
 * @return void
 */
function fg_antraege_save_meta_boxes( $post_id ) {
	if ( ! isset( $_POST['fg_antraege_nonce'] ) || ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['fg_antraege_nonce'] ) ), 'fg_antraege_save_meta' ) ) {
		return;
	}

	if ( ! current_user_can( 'edit_posts' ) ) {
		return;
	}

	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}

	if ( isset( $_POST['post_type'] ) && 'fg_antrag' !== sanitize_text_field( wp_unslash( $_POST['post_type'] ) ) ) {
		return;
	}

	$allowed_status = array( 'eingereicht', 'angenommen', 'abgelehnt' );

	if ( isset( $_POST['fg_status'] ) ) {
		$status = sanitize_text_field( wp_unslash( $_POST['fg_status'] ) );
		if ( ! in_array( $status, $allowed_status, true ) ) {
			$status = 'eingereicht';
		}
		update_post_meta( $post_id, '_fg_status', $status );
	}

	if ( isset( $_POST['fg_pdf_url'] ) ) {
		update_post_meta( $post_id, '_fg_pdf_url', esc_url_raw( wp_unslash( $_POST['fg_pdf_url'] ) ) );
	}
}
add_action( 'save_post_fg_antrag', 'fg_antraege_save_meta_boxes' );
