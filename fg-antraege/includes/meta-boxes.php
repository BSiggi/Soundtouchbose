<?php
/**
 * Meta Boxes for fg_antrag post type.
 *
 * @package FG_Antraege
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register meta boxes.
 */
function fg_antraege_add_meta_boxes() {
	add_meta_box(
		'fg_antrag_details',
		__( 'Antrag Details', 'fg-antraege' ),
		'fg_antraege_meta_box_callback',
		'fg_antrag',
		'normal',
		'high'
	);
}
add_action( 'add_meta_boxes', 'fg_antraege_add_meta_boxes' );

/**
 * Render the meta box HTML.
 *
 * @param WP_Post $post Current post object.
 */
function fg_antraege_meta_box_callback( $post ) {
	wp_nonce_field( 'fg_antraege_save_meta', 'fg_antraege_nonce' );

	$status = get_post_meta( $post->ID, '_fg_antrag_status', true );
	$datum  = get_post_meta( $post->ID, '_fg_antrag_datum', true );
	$pdf    = get_post_meta( $post->ID, '_fg_antrag_pdf', true );

	if ( empty( $status ) ) {
		$status = 'eingereicht';
	}
	?>
	<table class="form-table">
		<tr>
			<th scope="row">
				<label for="fg_antrag_status"><?php esc_html_e( 'Status', 'fg-antraege' ); ?></label>
			</th>
			<td>
				<select name="fg_antrag_status" id="fg_antrag_status">
					<option value="eingereicht" <?php selected( $status, 'eingereicht' ); ?>><?php esc_html_e( 'Eingereicht', 'fg-antraege' ); ?></option>
					<option value="angenommen" <?php selected( $status, 'angenommen' ); ?>><?php esc_html_e( 'Angenommen', 'fg-antraege' ); ?></option>
					<option value="abgelehnt" <?php selected( $status, 'abgelehnt' ); ?>><?php esc_html_e( 'Abgelehnt', 'fg-antraege' ); ?></option>
				</select>
			</td>
		</tr>
		<tr>
			<th scope="row">
				<label for="fg_antrag_datum"><?php esc_html_e( 'Datum (YYYY-MM-DD)', 'fg-antraege' ); ?></label>
			</th>
			<td>
				<input type="date" name="fg_antrag_datum" id="fg_antrag_datum"
					value="<?php echo esc_attr( $datum ); ?>"
					class="regular-text" />
			</td>
		</tr>
		<tr>
			<th scope="row">
				<label for="fg_antrag_pdf"><?php esc_html_e( 'PDF-Datei (URL)', 'fg-antraege' ); ?></label>
			</th>
			<td>
				<input type="text" name="fg_antrag_pdf" id="fg_antrag_pdf"
					value="<?php echo esc_url( $pdf ); ?>"
					class="regular-text" />
				<button type="button" class="button" id="fg_antrag_pdf_upload">
					<?php esc_html_e( 'PDF auswählen', 'fg-antraege' ); ?>
				</button>
				<p class="description"><?php esc_html_e( 'Wähle eine PDF-Datei aus der Medienbibliothek.', 'fg-antraege' ); ?></p>
			</td>
		</tr>
	</table>
	<?php
}

/**
 * Save meta box data.
 *
 * @param int $post_id Post ID.
 */
function fg_antraege_save_meta( $post_id ) {
	if ( ! isset( $_POST['fg_antraege_nonce'] ) ) {
		return;
	}
	if ( ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['fg_antraege_nonce'] ) ), 'fg_antraege_save_meta' ) ) {
		return;
	}
	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}
	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	$allowed_statuses = array( 'eingereicht', 'angenommen', 'abgelehnt' );

	if ( isset( $_POST['fg_antrag_status'] ) ) {
		$status = sanitize_text_field( wp_unslash( $_POST['fg_antrag_status'] ) );
		if ( in_array( $status, $allowed_statuses, true ) ) {
			update_post_meta( $post_id, '_fg_antrag_status', $status );
		}
	}

	if ( isset( $_POST['fg_antrag_datum'] ) ) {
		$datum = sanitize_text_field( wp_unslash( $_POST['fg_antrag_datum'] ) );
		/* Accept only YYYY-MM-DD format to ensure consistent storage and sorting. */
		if ( '' === $datum || preg_match( '/^\d{4}-\d{2}-\d{2}$/', $datum ) ) {
			update_post_meta( $post_id, '_fg_antrag_datum', $datum );
		}
	}

	if ( isset( $_POST['fg_antrag_pdf'] ) ) {
		$pdf = esc_url_raw( wp_unslash( $_POST['fg_antrag_pdf'] ) );
		update_post_meta( $post_id, '_fg_antrag_pdf', $pdf );
	}
}
add_action( 'save_post_fg_antrag', 'fg_antraege_save_meta' );

/**
 * Enqueue media uploader on fg_antrag edit screens.
 *
 * @param string $hook Current admin page hook.
 */
function fg_antraege_admin_enqueue( $hook ) {
	global $post;
	if ( ( 'post.php' === $hook || 'post-new.php' === $hook ) && isset( $post ) && 'fg_antrag' === $post->post_type ) {
		wp_enqueue_media();
		wp_enqueue_script(
			'fg-antraege-admin',
			FG_ANTRAEGE_URL . 'assets/fg-antraege-admin.js',
			array( 'jquery', 'media-upload' ),
			FG_ANTRAEGE_VERSION,
			true
		);
		wp_localize_script(
			'fg-antraege-admin',
			'fgAntraegeAdmin',
			array(
				'selectTitle'  => __( 'PDF auswählen', 'fg-antraege' ),
				'selectButton' => __( 'Auswählen', 'fg-antraege' ),
			)
		);
	}
}
add_action( 'admin_enqueue_scripts', 'fg_antraege_admin_enqueue' );
