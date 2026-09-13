class ApplicationController < ActionController::API
  include ActionController::Cookies
  include SessionOwnerGuard

  rescue_from ActiveRecord::RecordNotFound do
    render json: { error: ErrorCodes::NOT_FOUND }, status: :not_found
  end
end
